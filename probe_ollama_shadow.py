"""Explicit LIVE localhost probe. Temporary Core fixture, no production records."""
import json
import tempfile
import time
from pathlib import Path

from server import App, Run


def main():
    results = []
    with tempfile.TemporaryDirectory(prefix='jarvis-shadow-probe-') as folder:
        app = App(Path(folder))  # permitted isolated integration fixture, not a service
        app.ollama_shadow.enabled = True
        for text in ('what time is it', 'show my projects', 'what is the date'):
            run = Run('shadow-probe')
            app.work(run, text, None)
            worker = app.ollama_shadow.worker
            if worker:
                worker.join(25)
            if worker and worker.is_alive():
                raise RuntimeError('Shadow worker exceeded probe deadline')
            results.append({'fixture_command': text,
                            'core_completed': any(e['event'] == 'run.completed' for e in run.events),
                            'shadow': app.ollama_shadow.last if app.ollama_shadow.last and app.ollama_shadow.last['request_id'] == run.id else None,
                            'request_id': run.id})
            if app.ollama_shadow.last and app.ollama_shadow.last['error']:
                break  # no retries or bypassing failure cooldown
            time.sleep(5.1)
    print(json.dumps({'scope': 'LIVE Ollama plus temporary Core integration fixture; no desktop session test',
                      'results': results}, indent=2))


if __name__ == '__main__':
    main()
