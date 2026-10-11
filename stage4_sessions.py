"""STAGE4_TEST only: Core-owned transient ownership, not another auth service.

Only the trusted runtime may call attach_verified after Stage 2 authentication.
No network/body fields can create an authenticated enrollment. This module owns
no App, Store, provider, microphone, database, or process lifecycle.
"""
from dataclasses import dataclass, field
import hashlib
import secrets
import threading
import time


class Denied(Exception):
    """Bounded, non-disclosing control failure."""


def require(ok, reason='DENIED'):
    if not ok:
        raise Denied(reason)


def digest(token):
    require(type(token) is str and len(token) == 64)
    return hashlib.sha256(token.encode('ascii', errors='strict')).hexdigest()


@dataclass(frozen=True)
class Session:
    client: str
    family: str
    scopes: frozenset
    protocol: int
    generation: int
    expires: float
    recovery: bool = False


@dataclass
class Work:
    id: str
    family: str
    kind: str
    operation: str
    budget_ref: str | None
    phase: str = 'ADMITTED'
    cancel: threading.Event = field(default_factory=threading.Event)
    done: threading.Event = field(default_factory=threading.Event)
    outcome: str = 'UNKNOWN'


class Ownership:
    ORDINARY = frozenset({'attach', 'read', 'request', 'media'})
    MANAGEMENT = frozenset({'emergency', 'lifecycle'})

    def __init__(self, *, mode, epoch, enrollments, clock=time.monotonic,
                 session_seconds=900, lease_seconds=10):
        require(mode == 'STAGE4_TEST' and type(epoch) is str and bool(epoch), 'TEST_ONLY')
        require(0 < session_seconds <= 900 and 0 < lease_seconds <= 10, 'TEST_TIMERS')
        self.epoch = epoch
        self.clock = clock
        self.session_seconds, self.lease_seconds = session_seconds, lease_seconds
        self.lock = threading.RLock()  # Also the lifecycle admission barrier.
        self.enrollments = {name: frozenset(scopes) for name, scopes in enrollments.items()}
        require(all(s <= self.ORDINARY | self.MANAGEMENT for s in self.enrollments.values()), 'SCOPES')
        self.generations = {name: 0 for name in enrollments}
        self.disabled = set()
        self.sessions = {}
        self.work = {}
        self.leases = {}
        self.deliveries = set()
        self.capabilities = {}
        self.state = 'RUNNING'
        self.response_cancellations = None  # Trusted TEST runtime; I/O only outside lock.

    def flush_response_cancellations(self):
        if self.response_cancellations is not None:
            self.response_cancellations()

    def attach_verified(self, client, scopes, protocol):
        """Trusted bootstrap callback only; not exposed as a request operation."""
        with self.lock:
            self._expire()
            require(self.state == 'RUNNING', 'ADMISSION_CLOSED')
            require(client in self.enrollments and client not in self.disabled)
            require(type(protocol) is int and protocol in (2, 3), 'PROTOCOL')
            scopes = frozenset(scopes)
            require('attach' in scopes and scopes <= self.enrollments[client], 'SCOPE')
            require(len(self.sessions) < 128, 'SESSION_LIMIT')
            return self._issue(Session(client, secrets.token_hex(16), scopes, protocol,
                                       self.generations[client], self.clock()+self.session_seconds))

    def _issue(self, record):
        token = secrets.token_hex(32)
        self.sessions[digest(token)] = record
        return token

    def recover_verified(self, client, protocol):
        """Fresh authenticated lifecycle enrollment only; never ordinary admission."""
        with self.lock:
            self._expire()
            require(self.state in ('SUSPENDED','DRAINING','CANCELLING','RECOVERY_REQUIRED'), 'RECOVERY_STATE')
            require(client in self.enrollments and client not in self.disabled)
            scopes = frozenset({'attach','lifecycle'})
            require(scopes <= self.enrollments[client], 'SCOPE')
            require(type(protocol) is int and protocol in (2,3), 'PROTOCOL')
            require(len(self.sessions) < 128, 'SESSION_LIMIT')
            return self._issue(Session(client,secrets.token_hex(16),scopes,protocol,
                self.generations[client],self.clock()+self.session_seconds,recovery=True))

    def _expire(self):
        now = self.clock()
        for key, record in list(self.sessions.items()):
            if record.expires <= now:
                del self.sessions[key]
                self._cancel_family(record.family)
        for purpose, lease in list(self.leases.items()):
            if lease['expires'] <= now:
                del self.leases[purpose]

    def _session(self, token, epoch, scope=None):
        self._expire()
        require(epoch == self.epoch)
        s = self.sessions.get(digest(token))
        require(s is not None)
        require(s.client not in self.disabled and s.generation == self.generations[s.client])
        require(scope is None or scope in s.scopes, 'SCOPE')
        return s

    def renew_verified(self, token, epoch, authenticated_client):
        """Called only after fresh Stage 2 authentication of the same client."""
        with self.lock:
            s = self._session(token, epoch)
            require(s.client == authenticated_client)
            require(self.state == 'RUNNING' and not s.recovery, 'ADMISSION_CLOSED')
            del self.sessions[digest(token)]
            return self._issue(Session(s.client, s.family, s.scopes, s.protocol,
                                       s.generation, self.clock()+self.session_seconds))

    def _cancel_family(self, family):
        for w in self.work.values():
            if w.family == family and not w.done.is_set():
                w.cancel.set()
        self.leases = {p: l for p, l in self.leases.items() if l['family'] != family}
        self.capabilities = {k: c for k, c in self.capabilities.items() if c['family'] != family}

    def detach(self, token, epoch):
        with self.lock:
            s = self._session(token, epoch)
            del self.sessions[digest(token)]
            self._cancel_family(s.family)
        self.flush_response_cancellations()

    def revoke_client(self, client):
        """Trusted enrollment revocation, never a renderer-supplied admin flag."""
        with self.lock:
            require(client in self.enrollments)
            self.disabled.add(client)
            self.generations[client] += 1
            for key, s in list(self.sessions.items()):
                if s.client == client:
                    del self.sessions[key]
                    self._cancel_family(s.family)
        self.flush_response_cancellations()

    def admit(self, token, epoch, kind, *, operation=None, budget_ref=None):
        with self.lock:
            s = self._session(token, epoch, 'request')
            require(self.state == 'RUNNING', 'ADMISSION_CLOSED')
            require(kind in ('chat', 'tts', 'inspection', 'repair', 'local'), 'WORK_KIND')
            require(len(self.work) < 4096, 'WORK_LIMIT')
            if kind == 'chat':
                require(not any(w.kind == 'chat' and not w.done.is_set() for w in self.work.values()), 'BUSY')
            # Identifiers identify work, never grant execution/approval/budget authority.
            wid = secrets.token_hex(16)
            self.work[wid] = Work(wid, s.family, kind, operation or secrets.token_hex(16), budget_ref)
            return wid

    def _owned(self, token, epoch, wid):
        s = self._session(token, epoch)
        w = self.work.get(wid)
        require(w is not None and w.family == s.family)
        return w

    def check_owner(self, token, epoch, wid):
        """Apply before stream/upload/approval consumption, not only cancel."""
        with self.lock:
            return self._owned(token, epoch, wid).id

    def cancel_request(self, token, epoch, wid):
        with self.lock:
            w = self._owned(token, epoch, wid)
            w.cancel.set()
        # A successful acknowledgement must follow the durable response decision.
        self.flush_response_cancellations()
        return 'COMPLETED' if w.done.is_set() else 'CANCELLATION_REQUESTED'

    def begin(self, wid):
        """Trusted dispatcher gate, immediately before executing an authorized step."""
        with self.lock:
            self._expire()
            w = self.work[wid]
            require(self.state == 'RUNNING' and not w.cancel.is_set() and not w.done.is_set(), 'ADMISSION_CLOSED')
            require(any(s.family == w.family for s in self.sessions.values()))
            require(w.phase == 'ADMITTED', 'ALREADY_STARTED')
            w.phase = 'RUNNING'
            return w.cancel

    def next_step(self, wid):
        with self.lock:
            self._expire()
            w = self.work[wid]
            require(self.state == 'RUNNING' and w.phase == 'RUNNING' and not w.cancel.is_set(), 'ADMISSION_CLOSED')
            require(any(s.family == w.family for s in self.sessions.values()))

    def complete(self, wid, outcome):
        """Worker finally callback AFTER cleanup; cancellation is not completion."""
        with self.lock:
            require(outcome in ('SUCCEEDED', 'FAILED', 'NEVER_STARTED', 'UNKNOWN'), 'OUTCOME')
            w = self.work[wid]
            require(not w.done.is_set(), 'ALREADY_COMPLETED')
            require(outcome != 'NEVER_STARTED' or w.phase == 'ADMITTED', 'ALREADY_STARTED')
            w.outcome, w.phase = outcome, 'COMPLETED'
            w.done.set()

    def media(self, token, epoch, purpose, *, request_id=None, lease_id=None):
        with self.lock:
            s = self._session(token, epoch, 'media')
            require(self.state == 'RUNNING', 'ADMISSION_CLOSED')
            require(purpose in ('capture', 'playback'), 'MEDIA_PURPOSE')
            if purpose == 'playback':
                require(request_id is not None)
                self._owned(token, epoch, request_id)
            current = self.leases.get(purpose)
            if current:
                require(current['family'] == s.family and current['id'] == lease_id and current['request'] == request_id, 'BUSY')
                current['expires'] = min(s.expires, self.clock()+self.lease_seconds)
            else:
                require(lease_id is None, 'LEASE_EXPIRED')
                if purpose == 'playback':
                    require(request_id not in self.deliveries, 'ALREADY_DELIVERED')
                    self.deliveries.add(request_id)
                current = {'id': secrets.token_hex(16), 'family': s.family, 'request': request_id,
                           'expires': min(s.expires, self.clock()+self.lease_seconds)}
                self.leases[purpose] = current
            return {'id': current['id'], 'expires': current['expires'], 'epoch': self.epoch}

    def stop_media(self, token, epoch, purpose, lease_id):
        with self.lock:
            s = self._session(token, epoch)
            current = self.leases.get(purpose)
            require(current is not None and current['family'] == s.family and current['id'] == lease_id)
            del self.leases[purpose]

    def management_capability(self, token, epoch, action, operation):
        """Trusted native human controller only; never exposed to ordinary renderers."""
        with self.lock:
            scope = 'emergency' if action == 'emergency-stop' else 'lifecycle'
            s = self._session(token, epoch, scope)
            require(action in ('shutdown', 'emergency-stop'), 'ACTION')
            require(type(operation) is str and 1 <= len(operation) <= 80, 'OPERATION')
            require(len(self.capabilities) < 128, 'CAPABILITY_LIMIT')
            capability = secrets.token_hex(32)
            self.capabilities[digest(capability)] = {'family': s.family, 'action': action,
                'operation': operation, 'expires': min(s.expires, self.clock()+30)}
            return capability

    def consume_management(self, token, epoch, capability, action, operation):
        with self.lock:
            s = self._session(token, epoch, 'emergency' if action == 'emergency-stop' else 'lifecycle')
            key = digest(capability)
            c = self.capabilities.get(key)
            require(c is not None and c['family'] == s.family and c['expires'] > self.clock()
                    and c['action'] == action and c['operation'] == operation)
            del self.capabilities[key]

    def snapshot(self):
        """Memory-only status. No tokens, request content or Store refresh side effects."""
        with self.lock:
            self._expire()
            return {'epoch': self.epoch, 'state': self.state, 'sessions': len(self.sessions),
                    'active_work': sum(not w.done.is_set() for w in self.work.values()),
                    'media': sorted(self.leases), 'budget_enforcement': 'NOT_UNIVERSAL'}
