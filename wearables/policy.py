"""In-process development authorization. Not a network authentication service."""
import secrets
import time
from .contracts import WearableError, identifier


class Policy:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.sessions = {}

    def issue(self, device_id, scopes=frozenset({'look'}), ttl=300):
        if not 0 < ttl <= 300 or not set(scopes) <= {'look'}:
            raise WearableError('INVALID_SCOPE')
        token = secrets.token_urlsafe(32)
        self.sessions[token] = (identifier(device_id), frozenset(scopes), self.clock()+ttl)
        return token

    def revoke(self, token):
        self.sessions.pop(token, None)

    def check(self, token, device_id, operation):
        row = self.sessions.get(token) if isinstance(token, str) else None
        if not row or self.clock() >= row[2]:
            raise WearableError('UNAUTHENTICATED')
        if row[0] != device_id or operation not in row[1]:
            raise WearableError('FORBIDDEN')
