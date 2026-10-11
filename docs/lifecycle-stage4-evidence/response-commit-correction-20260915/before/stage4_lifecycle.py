"""STAGE4_TEST admission/drain control. Never releases a Core lifetime lock.

Pure ownership/drain control plus an isolated content-free operation journal.
The runtime must track actual workers and retain core.lock until process exit.
"""
import json
import os
from pathlib import Path
import stat
import threading
import uuid

from stage4_sessions import Denied, require


class Journal:
    def __init__(self, root, identity):
        self.root = Path(os.path.abspath(root))
        self.identity = dict(identity)
        require(identity.get('mode') == 'STAGE4_TEST', 'TEST_ONLY')
        require(self.root.name.startswith('STAGE4_TEST-'), 'TEST_PATH')
        for p in (self.root, *self.root.parents):
            st = p.lstat()
            require(not stat.S_ISLNK(st.st_mode) and not getattr(st, 'st_file_attributes', 0) & 0x400, 'REPARSE_PATH')
        require((self.root/'STAGE4_TEST.json').read_text() == json.dumps(identity, sort_keys=True), 'TEST_IDENTITY')
        self.lock = threading.Lock()

    def write(self, operation, phase, *, kind, budget_ref=None):
        require(type(operation) is str and len(operation) == 32 and all(c in '0123456789abcdef' for c in operation), 'OPERATION')
        require(phase in ('ADMITTED', 'RUNNING', 'SUCCEEDED', 'FAILED', 'UNKNOWN', 'NEVER_STARTED', 'STOP_INTENT', 'RECOVERY_REQUIRED'), 'PHASE')
        require(kind in ('chat', 'tts', 'inspection', 'repair', 'local', 'shutdown', 'emergency-stop'), 'KIND')
        require(budget_ref is None or type(budget_ref) is str and len(budget_ref) <= 128, 'BUDGET_REFERENCE')
        record = {'identity': self.identity, 'operation': operation, 'phase': phase,
                  'kind': kind, 'budget_ref': budget_ref, 'replay_authorized': False}
        with self.lock:
            target = self.root/(operation+'.json')
            if target.exists():
                st = target.lstat()
                require(not stat.S_ISLNK(st.st_mode) and not getattr(st, 'st_file_attributes', 0) & 0x400, 'REPARSE_PATH')
            temp = self.root/(operation+'.'+uuid.uuid4().hex+'.tmp')
            # A failed write/replace is retained for review. No retry or delete.
            with temp.open('x', encoding='utf8') as f:
                json.dump(record, f, sort_keys=True)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp, target)

    def inspect(self):
        records = []
        with self.lock:
            require(not list(self.root.glob('*.tmp')), 'RECOVERY_REQUIRED')
            for p in self.root.glob('*.json'):
                if p.name == 'STAGE4_TEST.json':
                    continue
                st = p.lstat()
                require(not stat.S_ISLNK(st.st_mode) and not getattr(st, 'st_file_attributes', 0) & 0x400, 'REPARSE_PATH')
                try:
                    record = json.loads(p.read_text())
                    require(record['identity'] == self.identity and record['replay_authorized'] is False, 'JOURNAL_IDENTITY')
                    require(set(record) == {'identity', 'operation', 'phase', 'kind', 'budget_ref', 'replay_authorized'}, 'JOURNAL_SCHEMA')
                    require(p.stem == record['operation'], 'JOURNAL_OPERATION')
                    require(record['phase'] in ('SUCCEEDED', 'FAILED', 'NEVER_STARTED'), 'RECOVERY_REQUIRED')
                except (ValueError, KeyError, TypeError) as e:
                    raise Denied('JOURNAL_CORRUPT') from e
                records.append(record)
        return records


class Lifecycle:
    def __init__(self, ownership, journal):
        self.owners, self.journal = ownership, journal
        self.workers = {}
        self.transactions = {}
        self.accepted_at = None
        self.intent_pending = False
        self.failure = None

    def _recovery(self, reason):
        with self.owners.lock:
            self.owners.state = 'RECOVERY_REQUIRED'
            self.failure = reason
            for record in self.transactions.values():record['failed']=True
            for w in self.owners.work.values():
                if not w.done.is_set():
                    w.cancel.set()
            self.owners.leases.clear()

    def dispatch(self, token, epoch, kind, function, *, budget_ref=None):
        """function(cancel) includes final cleanup and returns a known outcome.

        Only a trusted, already-authorized dispatcher supplies function. This is
        not an execution endpoint and does not bypass tool/approval/budget gates.
        """
        with self.owners.lock:
            wid = self.owners.admit(token, epoch, kind, budget_ref=budget_ref)
            w = self.owners.work[wid]
            thread = threading.Thread(target=self._work, args=(w, function), daemon=True)
            self.workers[wid] = thread
        try:
            self.journal.write(w.id, 'ADMITTED', kind=w.kind, budget_ref=w.budget_ref)
            thread.start()
        except Exception:
            self._recovery('ACCEPTANCE_PERSISTENCE_OR_START_FAILED')
            raise
        return wid

    def _work(self, w, function):
        try:
            # Persist attempt BEFORE any effect. Stop/disappearance never refunds.
            self.journal.write(w.id, 'RUNNING', kind=w.kind, budget_ref=w.budget_ref)
            try:
                cancel = self.owners.begin(w.id)
            except Denied:
                outcome = 'NEVER_STARTED'
            else:
                outcome = function(cancel)
                require(outcome in ('SUCCEEDED', 'FAILED', 'UNKNOWN'), 'OUTCOME')
            self.journal.write(w.id, outcome, kind=w.kind, budget_ref=w.budget_ref)
            self.owners.complete(w.id, outcome)
        except Exception:
            # Actual worker unwinds; no invented outcome or successful settlement.
            self._recovery('WORK_OR_OUTCOME_PERSISTENCE_FAILED')

    def request(self, token, epoch, capability, action, operation):
        with self.owners.lock:
            scope = 'emergency' if action == 'emergency-stop' else 'lifecycle'
            s = self.owners._session(token, epoch, scope)
            prior = self.transactions.get(operation)
            if prior:
                require(prior['family'] == s.family and prior['action'] == action)
                return self.status()
            self.owners.consume_management(token, epoch, capability, action, operation)
            if self.owners.state == 'RECOVERY_REQUIRED':
                # Only a new explicit owner request may re-evaluate a deadline
                # quarantine. Persistence failures/unknown outcomes remain blocked.
                require(action == 'shutdown' and self.failure == 'SHUTDOWN_DEADLINE_OR_UNKNOWN_OUTCOME'
                        and not self.intent_pending and all(w.done.is_set() and w.outcome != 'UNKNOWN' for w in self.owners.work.values())
                        and not any(t.is_alive() for t in self.workers.values()), 'RECOVERY_UNRESOLVED')
            else:
                require(self.owners.state == 'RUNNING' or self.owners.state == 'SUSPENDED' and action == 'shutdown', 'ADMISSION_CLOSED')
            require(len(operation) == 32 and all(c in '0123456789abcdef' for c in operation), 'OPERATION')
            self.transactions[operation] = {'family': s.family, 'action': action}
            self.accepted_at = self.owners.clock()
            self.failure = None
            self.intent_pending = True
            self.owners.state = 'SUSPENDED' if action == 'emergency-stop' else 'DRAINING'
            self.owners.leases.clear()
            for w in self.owners.work.values():
                if action == 'emergency-stop' or w.phase == 'ADMITTED' or w.kind == 'chat':
                    w.cancel.set()
        try:
            self.journal.write(operation, 'STOP_INTENT', kind=action)
        except Exception:
            self._recovery('STOP_INTENT_PERSISTENCE_FAILED')
        finally:
            with self.owners.lock:
                self.intent_pending = False
        return self.status()

    def tick(self):
        """Nonblocking drain observation; never joins or kills a worker."""
        with self.owners.lock:
            self.owners._expire()
            if self.owners.state not in ('DRAINING', 'CANCELLING'):
                return self.status()
            elapsed = self.owners.clock()-self.accepted_at
            if elapsed >= 10:
                self.owners.state = 'CANCELLING'
                for w in self.owners.work.values():
                    if not w.done.is_set():
                        w.cancel.set()
            active = self.intent_pending or any(not w.done.is_set() for w in self.owners.work.values()) or any(t.is_alive() for t in self.workers.values())
            uncertain = any(w.outcome == 'UNKNOWN' for w in self.owners.work.values())
            if not active and not uncertain:
                # Runtime still must close listeners/resources, then EXIT while
                # retaining core.lock. This is never a claim that Core has exited.
                self.owners.state = 'FINALIZING'
                for key, s in list(self.owners.sessions.items()):
                    if not s.scopes & self.owners.MANAGEMENT:
                        del self.owners.sessions[key]
            elif elapsed >= 30:
                self._recovery('SHUTDOWN_DEADLINE_OR_UNKNOWN_OUTCOME')
            return self.status()

    def status(self):
        with self.owners.lock:
            return {**self.owners.snapshot(), 'failure': self.failure,
                    'intent_persisted': self.accepted_at is not None and not self.intent_pending and self.failure != 'STOP_INTENT_PERSISTENCE_FAILED',
                    'core_exit_verified': False, 'budget_refunds_performed': False}

    def record_exit_ready(self):
        """Record drained operations after runtime listener/control-worker closure.

        This is not OS-exit evidence. A write failure retains Core ownership.
        """
        with self.owners.lock:
            require(self.owners.state == 'FINALIZING' and not self.intent_pending)
            require(all(w.done.is_set() and w.outcome != 'UNKNOWN' for w in self.owners.work.values()))
            require(not any(t.is_alive() for t in self.workers.values()))
            operations=list(self.transactions.items())
        try:
            for operation,record in operations:
                self.journal.write(operation,'FAILED' if record.get('failed') else 'SUCCEEDED',kind=record['action'])
        except Exception:
            self._recovery('EXIT_READINESS_PERSISTENCE_FAILED')
            raise
