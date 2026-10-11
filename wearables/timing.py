import time


class Timing:
    """Durations from one process clock only. Never invent provider token timings."""
    def __init__(self):
        self.started = time.perf_counter()
        self.events = {}

    def mark(self, name):
        self.events[name] = round((time.perf_counter()-self.started)*1000, 3)

    def report(self):
        return {'simulated': True, 'clock': 'local_monotonic', 'events_ms': dict(self.events),
                'AI_first_token_ms': None, 'network_ms': None}
