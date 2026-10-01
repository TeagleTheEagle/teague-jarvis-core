"""Bounded TEST ONLY diagnosis -> candidate -> sandbox -> review workflow.

Reuses existing Core client and experiment contracts. No production deployment,
new provider, persistent worker, canonical task database or assistant instance.
"""
import asyncio
import difflib
import hashlib
import json
from pathlib import Path
import threading
import time
import uuid

from repair_trial import BEFORE, CASES, validate_candidate
from repair_sandbox import check_candidate
from wearables.real_core import RealCore


def parse_answer(answer):
    if not isinstance(answer, str) or len(answer) > 5000:
        raise ValueError('Response size rejected.')
    answer = answer.strip()
    if answer.startswith('```json\n') and answer.endswith('```'):
        answer = answer[8:-3].strip()
    item = json.loads(answer)
    if type(item) is not dict or set(item) != {'diagnosis', 'candidate'}:
        raise ValueError('Expected diagnosis and candidate only.')
    if not isinstance(item['diagnosis'], str) or not 1 <= len(item['diagnosis']) <= 1000:
        raise ValueError('Diagnosis size rejected.')
    validate_candidate(item['candidate'])
    return item


async def run(core, cancel=None, checker=check_candidate, seconds=180):
    if type(seconds) not in (int, float) or not 1 <= seconds <= 180:
        raise ValueError('Workflow deadline must be 1..180 seconds.')
    cancel = cancel if cancel is not None else threading.Event()
    started = time.monotonic()
    deadline = started + seconds
    report = {'test_only': True, 'deployed': False, 'status': 'RUNNING',
              'core': 'existing authoritative JARVIS', 'events': [],
              'resources': {'core_requests': 0, 'max_core_requests': 1,
                            'container_checks': 0, 'max_container_checks': 2,
                            'retries': 0, 'purchases': 0, 'cost_usd': None,
                            'deadline_seconds': seconds}}

    def event(state):
        report['events'].append({'state': state, 'elapsed_ms': round((time.monotonic()-started)*1000, 2)})

    def checkpoint():
        if cancel.is_set():
            raise InterruptedError()
        if time.monotonic() >= deadline:
            cancel.set()
            raise TimeoutError()

    async def checked(source):
        checkpoint()
        if report['resources']['container_checks'] >= 2:
            raise RuntimeError('Container budget exceeded.')
        report['resources']['container_checks'] += 1
        task = asyncio.create_task(asyncio.to_thread(checker, source, cancel))
        try:
            while not task.done():
                checkpoint()
                await asyncio.sleep(.05)
            result = await task
            checkpoint()
            return result
        finally:
            if not task.done():
                cancel.set()
                await asyncio.shield(task)  # Do not abandon guest cleanup.

    try:
        event('BASELINE')
        baseline = await checked(BEFORE)
        report['baseline'] = baseline
        # A transport failure is not a diagnosed code defect.
        if (baseline.get('execution_status') != 'EXITED' or baseline.get('exit_code') != 0 or
                baseline.get('cleanup') is not True or baseline.get('runtime_values') != [x for x, _ in CASES]):
            raise RuntimeError('Baseline execution not verified.')
        failures = [{'input': x, 'expected': target, 'actual': actual}
                    for (x, target), actual in zip(CASES, baseline['runtime_values']) if actual != target]
        if not failures:
            report['status'] = 'NO_REPAIR_NEEDED'
            return report
        report['observed_failures'] = failures
        event('DIAGNOSIS_AND_PATCH')
        checkpoint()
        prompt = ('TEST ONLY review exercise. Do not use tools, read projects or modify files. '
                  'Diagnose this fixture using the observed test failures and propose a repair. '
                  'Reply ONLY with JSON containing diagnosis (short string) and candidate (Python source). '
                  'Required behavior: negative numeric delays become zero; nonnegative values stay unchanged. '
                  'Allowed source: one def delay(seconds), one return expression using seconds, bounded '
                  'numeric constants, unary minus, min/max with two arguments. No other syntax.\n'
                  'Source:\n' + BEFORE + '\nObserved failures: ' + json.dumps(failures))
        report['resources']['core_requests'] += 1
        task = asyncio.create_task(core.respond(prompt, conversation='wearable-repair-workflow-'+uuid.uuid4().hex))
        try:
            while not task.done():
                checkpoint()
                await asyncio.sleep(.1)
            answer = await task
            checkpoint()
        finally:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        proposal = parse_answer(answer)
        report.update(proposal)
        event('SANDBOX_VERIFICATION')
        result = await checked(proposal['candidate'])
        report['verification'] = result
        checkpoint()
        if result.get('status') == 'READY_FOR_REVIEW' and result.get('cleanup') is True:
            report['diff'] = ''.join(difflib.unified_diff(BEFORE.splitlines(True), proposal['candidate'].splitlines(True),
                                                       fromfile='TEST_ONLY/delay.py', tofile='TEST_ONLY/delay.py'))
            report['candidate_sha256'] = hashlib.sha256(proposal['candidate'].encode()).hexdigest()
            report['status'] = 'READY_FOR_REVIEW'
        else:
            report['status'] = 'REJECTED'
    except InterruptedError:
        report['status'] = 'CANCELLED'
    except TimeoutError:
        report['status'] = 'DEADLINE_EXCEEDED'
    except Exception as exc:
        report['status'] = 'FAILED'
        report['error_type'] = type(exc).__name__  # No credentials/raw service errors.
    finally:
        event(report['status'])
        report['elapsed_seconds'] = round(time.monotonic()-started, 3)
    return report


if __name__ == '__main__':
    # Explicit invocation incurs one normal request through the existing Core.
    try:
        result = asyncio.run(run(RealCore()))
    except Exception as exc:
        result = {'status': 'FAILED', 'error_type': type(exc).__name__, 'deployed': False}
    path = Path(__file__).parent/'docs'/'repair-workflow-results.json'
    path.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['status'] == 'READY_FOR_REVIEW' else 1)
