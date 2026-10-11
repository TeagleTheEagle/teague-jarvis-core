"""Strict TEST adapter over the unchanged bounded heartbeat journal."""
import json
from journal import Reader, PublisherWatch, Unhealthy, ticks, frequency
from workspace import check_path

class HealthReader:
    def __init__(self, root, ready, *, clock=ticks, watch_factory=PublisherWatch):
        self.root = check_path(root)
        self.failed = False
        self.watch = None
        self.reader = None
        self.closed = False
        self.clock = clock
        if type(ready.get('pid')) is not int or ready['pid'] <= 0:
            raise Unhealthy('Invalid publisher PID')
        if type(ready.get('frequency')) is not int or ready['frequency'] != frequency():
            raise Unhealthy('Publisher frequency mismatch')
        if not isinstance(ready.get('created'), str) or not ready['created'].isdigit() or int(ready['created']) <= 0:
            raise Unhealthy('Invalid publisher creation identity')
        self.identity = dict(run=self.root.name, pid=ready['pid'], created=ready['created'], frequency=ready['frequency'])
        try:
            self.watch = watch_factory(self.identity)
            self.reader = Reader(check_path(self.root/'app-health.jsonl'), self.identity, clock, self.watch.check)
        except BaseException:
            self.close()
            raise

    def poll(self):
        if self.failed or self.closed:
            raise Unhealthy('Health reader unavailable')
        try:
            result = self.reader.poll()
            self.watch.check()
            if not 0 <= result['age'] < 10:
                raise Unhealthy('Strict ten-second health boundary')
            return result
        except BaseException:
            self.failed = True
            raise

    def finalize(self):
        """Offline closure only after the launcher confirms observer exit."""
        if self.failed or self.closed:
            raise Unhealthy('Failed reader cannot finalize successfully')
        try:
            release = json.loads((self.root/'release-handles').read_text(encoding='utf-8-sig'))
            result = json.loads((self.root/'app-result.json').read_text(encoding='utf-8-sig'))
            if release.get('observerExited') is not True or result.get('success') is not True or result.get('durableFinalization') is not True:
                raise Unhealthy('Publisher closure not proven')
            # Closure is not a new live health observation. Retain all content,
            # sequence and file-identity checks without requiring the exited publisher.
            self.reader.liveness = None
            self.reader.clock = lambda: self.reader.last['ticks'] if self.reader.last else self.clock()
            self.reader.poll()
            if self.reader.pending:
                raise Unhealthy('Incomplete final health record')
            return dict(sequence=self.reader.sequence, complete=True)
        except BaseException:
            self.failed = True
            raise

    def close(self):
        try:
            if self.reader is not None:
                self.reader.close()
        finally:
            if self.watch is not None:
                self.watch.close()
            self.closed = True
