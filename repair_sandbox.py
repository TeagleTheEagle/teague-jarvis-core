"""TEST ONLY rootless controller. No Core, provider, memory or deployment owner.

Public repair entry point accepts only the existing validated numeric fixture.
The private execution primitive is for reviewed isolation probes, not model tools.
"""
import hashlib
import json
import os
import subprocess
import threading
import time
import uuid

from repair_trial import CASES, evaluate, validate_candidate

IMAGE = '28eb0cb65acb65b970e85c0dc57d10067868fae8dd00d072413df273132123ac'
PREFIX = ['wsl.exe', '-d', 'Ubuntu-24.04', '-u', 'jarvis-repair',
          '--exec', '/usr/bin/podman']
OUTPUT_LIMIT = 16384


def environment():
    # No inherited WSLENV, provider tokens, proxy configuration or Python paths.
    return {key: os.environ[key] for key in ('SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP')
            if key in os.environ}


def control(args):
    return subprocess.run(PREFIX + args, stdin=subprocess.DEVNULL,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          env=environment(), timeout=20,
                          creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))


def preflight():
    result = control(['info', '--format=json'])
    if result.returncode:
        raise RuntimeError('Rootless runtime unavailable.')
    host = json.loads(result.stdout)['host']
    if (host['security']['rootless'] is not True or
            host['security']['seccompEnabled'] is not True or
            host['cgroupVersion'] != 'v2' or
            not {'cpu', 'memory', 'pids'} <= set(host['cgroupControllers'])):
        raise RuntimeError('Required isolation controls unavailable.')


def create_args(name, seconds):
    return ['create', '--name', name, '--pull=never', '--network=none',
            '--read-only', '--read-only-tmpfs=false', '--cap-drop=ALL',
            '--security-opt=no-new-privileges', '--user=65534:65534',
            '--pids-limit=32', '--memory=128m', '--memory-swap=128m',
            '--cpus=0.5', '--log-driver=none', '--http-proxy=false',
            '--env=HOME=/nonexistent', '--env=PATH=/usr/local/bin:/usr/bin:/bin',
            '--ulimit=nofile=64:64', '--ulimit=core=0:0',
            '--timeout=' + str(seconds), '-i', IMAGE,
            '/usr/local/bin/python3', '-I', '-']


def _execute_probe(script, cancel=None, seconds=10):
    """Run reviewed test code; never expose this primitive as a JARVIS tool."""
    if type(seconds) is not int or not 1 <= seconds <= 15:
        raise ValueError('Container budget must be 1..15 whole seconds.')
    payload = script.encode('utf-8')
    if len(payload) > 8192:
        raise ValueError('Input exceeds 8 KiB.')
    cancel = cancel if cancel is not None else threading.Event()
    if cancel.is_set():
        return {'status': 'CANCELLED', 'cleanup': True, 'output': '', 'exit_code': None}
    preflight()
    name = 'jarvis-repair-' + uuid.uuid4().hex
    started = time.monotonic()
    child = None
    overflow = threading.Event()
    output = bytearray()
    result = None
    try:
        if control(create_args(name, seconds)).returncode:
            raise RuntimeError('Restricted container creation failed.')
        if cancel.is_set():
            result = {'status': 'CANCELLED', 'output': '', 'exit_code': None}
        else:
            child = subprocess.Popen(PREFIX + ['start', '-a', '-i', name],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, env=environment(),
                                     creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            def read():
                while True:
                    chunk = child.stdout.read(1024)
                    if not chunk:
                        break
                    room = OUTPUT_LIMIT - len(output)
                    output.extend(chunk[:room])
                    if len(chunk) > room:
                        overflow.set()
            reader = threading.Thread(target=read, daemon=True)
            reader.start()
            # Payload is bounded below pipe capacity; no caller filenames/mounts.
            child.stdin.write(payload)
            child.stdin.close()
            deadline = time.monotonic() + seconds + 5
            status = 'EXITED'
            while child.poll() is None:
                if cancel.is_set():
                    status = 'CANCELLED'
                    break
                if overflow.is_set():
                    status = 'OUTPUT_LIMIT'
                    break
                if time.monotonic() >= deadline:
                    status = 'TIMEOUT'
                    break
                time.sleep(.02)
            if child.poll() is None:
                # Killing wsl.exe alone leaves the guest/container alive. Stop the
                # owned execution unit first so attached pipes close promptly.
                if control(['rm', '--force', '--time=0', '--ignore', name]).returncode:
                    raise RuntimeError('Container stop failed.')
                child.kill()
                child.wait(timeout=5)
            reader.join(timeout=2)
            if overflow.is_set() and status == 'EXITED':
                status = 'OUTPUT_LIMIT'
            result = {'status': status, 'exit_code': child.returncode,
                      'output': output.decode('utf-8', errors='replace')}
    finally:
        # Stop guest work BEFORE closing attached pipes (which can otherwise wait
        # for guest EOF after the Windows WSL client has already been killed).
        removed = control(['rm', '--force', '--time=0', '--ignore', name])
        if child is not None:
            if child.poll() is None:
                child.kill()
                child.wait(timeout=5)
            if child.stdin and not child.stdin.closed:
                child.stdin.close()
            child.stdout.close()
        # Remove only this invocation's UUID container, including descendants.
        exists = control(['container', 'exists', name])
        if removed.returncode or exists.returncode != 1:
            raise RuntimeError('Container cleanup unverified; stop further experiments.')
    result.update(cleanup=True, elapsed_seconds=round(time.monotonic()-started, 3))
    return result


def check_candidate(source, cancel=None):
    expression = validate_candidate(source)  # Reject general Python BEFORE runtime.
    expected = [target for _, target in CASES]
    independent = [evaluate(expression, value) for value, _ in CASES]
    # Validated function cannot alter test harness, print, import or access files.
    script = ('import json\n' + source + '\nprint(json.dumps([delay(x) for x in ' +
              repr([value for value, _ in CASES]) + ']))\n')
    result = _execute_probe(script, cancel)
    runtime = None
    if result['status'] == 'EXITED' and result['exit_code'] == 0:
        try:
            runtime = json.loads(result['output'])
        except (ValueError, TypeError):
            pass
    passed = (type(runtime) is list and len(runtime) == len(expected) and
              all(type(x) in (int, float) for x in runtime) and
              runtime == independent == expected)
    return {**result, 'status': 'READY_FOR_REVIEW' if passed else 'NOT_ACCEPTED',
            'execution_status': result['status'], 'runtime_values': runtime,
            'independent_passed': sum(a == b for a, b in zip(independent, expected)),
            'total': len(expected), 'candidate_sha256': hashlib.sha256(source.encode()).hexdigest(),
            'deployed': False, 'provider_calls': 0, 'test_only': True}
