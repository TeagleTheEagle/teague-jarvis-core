"""TEST ONLY: fixed local fixture experiment. No App, provider, memory or deployment.

This is process separation, NOT an OS sandbox for arbitrary generated code.
Only the hard-coded fixture and hard-coded candidate below are executed.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time

import development

OBJECTIVE = 'Correct negative delay handling in the isolated test fixture.'
BEFORE = 'def delay(seconds):\n    return seconds\n'
AFTER = 'def delay(seconds):\n    return max(0, seconds)\n'
CHECKS = '''
import runpy, sys
delay = runpy.run_path(sys.argv[1])['delay']
cases = [(-5, 0), (0, 0), (2, 2), (0.5, 0.5)]
failures = sum(delay(value) != expected for value, expected in cases)
print(f'{len(cases)-failures}/{len(cases)} checks passed')
sys.exit(bool(failures))
'''


def checkpoint(cancel, deadline, clock=time.monotonic):
    if cancel.is_set():
        raise InterruptedError('Experiment cancelled; no deployment.')
    if clock() >= deadline:
        raise TimeoutError('Experiment time budget exhausted; no deployment.')


def check_fixture(root, filename, cancel, deadline):
    checkpoint(cancel, deadline)
    # Do not inherit provider credentials; no shell or model-generated command.
    env = {k: os.environ[k] for k in ('SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP') if k in os.environ}
    with subprocess.Popen(
        [sys.executable, '-I', str(root / 'checks.py'), str(root / filename)],
        cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
    ) as child:
        try:
            while True:
                checkpoint(cancel, deadline)
                try:
                    stdout, stderr = child.communicate(timeout=0.05)
                    checkpoint(cancel, deadline)
                    return {'exit_code': child.returncode, 'summary': stdout.strip(), 'error': stderr[-1000:]}
                except subprocess.TimeoutExpired:
                    continue
        finally:
            if child.poll() is None:
                child.kill()
                child.communicate()


def run_experiment(cancel=None, seconds=10):
    if not isinstance(seconds, (int, float)) or not 0 < seconds <= 30:
        raise ValueError('Budget must be greater than zero and at most 30 seconds.')
    cancel = cancel if cancel is not None else threading.Event()
    started = time.monotonic()
    deadline = started + seconds
    checkpoint(cancel, deadline)
    with tempfile.TemporaryDirectory(prefix='jarvis-fixed-experiment-') as folder:
        root = Path(folder)
        # wake.py is an allowlisted filename in the EXISTING proposal mechanism;
        # this temporary fixture is unrelated to production wake-word code.
        (root / 'wake.py').write_text(BEFORE, encoding='utf-8')
        (root / 'checks.py').write_text(CHECKS, encoding='utf-8')
        baseline = check_fixture(root, 'wake.py', cancel, deadline)
        if baseline['exit_code'] != 1 or baseline['summary'] != '3/4 checks passed':
            raise RuntimeError('Unexpected baseline; experiment stopped.')
        checkpoint(cancel, deadline)
        proposal = development.prepare(root, 'wake.py', AFTER, OBJECTIVE)
        staged = root / 'data' / 'development' / proposal['proposal'] / 'candidate.txt'
        if staged.read_text(encoding='utf-8') != AFTER:
            raise ValueError('Candidate differs from the fixed reviewed fixture.')
        candidate = check_fixture(root, str(staged.relative_to(root)), cancel, deadline)
        checkpoint(cancel, deadline)
        unchanged = (root / 'wake.py').read_text(encoding='utf-8') == BEFORE
        passed = candidate['exit_code'] == 0 and candidate['summary'] == '4/4 checks passed' and unchanged
        return {
            'test_only': True, 'objective': OBJECTIVE,
            'subgoals': ['Establish failing baseline', 'Stage fixed patch', 'Run unchanged checks', 'Return diff for review'],
            'status': 'READY_FOR_REVIEW' if passed else 'FAILED',
            'baseline': baseline, 'candidate': candidate, 'diff': proposal['diff'],
            'source_unchanged': unchanged, 'deployment': 'NOT IMPLEMENTED',
            'resources': {'provider_calls': 0, 'purchases': 0, 'child_runs': 2, 'max_child_runs': 2, 'budget_seconds': seconds},
            'elapsed_seconds': round(time.monotonic() - started, 3),
        }


if __name__ == '__main__':
    try:
        print(json.dumps(run_experiment(), indent=2))
    except (InterruptedError, TimeoutError, KeyboardInterrupt) as exc:
        print(json.dumps({'status': 'STOPPED', 'reason': str(exc)}))
        sys.exit(1)
