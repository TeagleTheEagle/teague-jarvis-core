"""Explicit live-service checks. Trusted probes only; not unittest discovery."""
import json
from pathlib import Path
import threading
import time
import repair_sandbox as r


def main():
    evidence = {}
    saved = json.loads((Path(__file__).parent/'docs/repair-trial-result.json').read_text())
    evidence['baseline'] = r.check_candidate('def delay(seconds):\n return seconds\n')
    evidence['previous_real_core_candidate'] = r.check_candidate(saved['candidate'])
    probe = '''import os, socket, json
checks = {}
checks['nonroot'] = os.getuid() != 0
checks['no_windows_mount'] = not os.path.exists('/mnt/c')
checks['no_socket'] = not os.path.exists('/run/user/1000/podman/podman.sock')
checks['no_credentials'] = not any(k in os.environ for k in ['OPENAI_API_KEY','WSLENV','HTTP_PROXY'])
try:
    open('/tmp/test-write', 'w').close()
    checks['readonly'] = False
except OSError:
    checks['readonly'] = True
s = socket.socket()
s.settimeout(.5)
try:
    s.connect(('192.0.2.1', 443))
    checks['network_denied'] = False
except OSError:
    checks['network_denied'] = True
checks['memory_limit'] = open('/sys/fs/cgroup/memory.max').read().strip() == '134217728'
checks['pids_limit'] = open('/sys/fs/cgroup/pids.max').read().strip() == '32'
print(json.dumps(checks))
'''
    evidence['isolation'] = r._execute_probe(probe)
    evidence['output_limit'] = r._execute_probe("import os\nwhile True: os.write(1,b'x'*4096)\n")
    evidence['timeout'] = r._execute_probe('import time\ntime.sleep(30)\n', seconds=2)
    evidence['memory_exhaustion'] = r._execute_probe('blocks=[]\nwhile True: blocks.append(bytearray(16*1024*1024))\n')
    evidence['process_limit'] = r._execute_probe('''import subprocess, json
children=[]
denied=False
try:
    for _ in range(64):
        children.append(subprocess.Popen(['/bin/sleep','5']))
except OSError:
    denied=True
finally:
    for child in children:
        child.terminate()
    for child in children:
        child.wait()
print(json.dumps({'denied':denied,'children':len(children)}))
''')
    stop = threading.Event()
    timer = threading.Timer(3, stop.set)
    timer.start()
    try:
        evidence['cancel'] = r._execute_probe('import time\ntime.sleep(30)\n', stop)
    finally:
        timer.cancel()
    # Candidate data and raw output are untrusted; only explicit checks count.
    checks = json.loads(evidence['isolation']['output'])
    passed = (evidence['baseline']['status'] == 'NOT_ACCEPTED' and
              evidence['previous_real_core_candidate']['status'] == 'READY_FOR_REVIEW' and
              all(checks.values()) and
              evidence['output_limit']['status'] == 'OUTPUT_LIMIT' and
              evidence['timeout']['exit_code'] != 0 and
              evidence['memory_exhaustion']['exit_code'] != 0 and
              json.loads(evidence['process_limit']['output'])['denied'] and
              evidence['cancel']['status'] == 'CANCELLED' and
              evidence['cancel']['elapsed_seconds'] < 8 and
              all(v['cleanup'] for v in evidence.values()))
    evidence['output_limit']['output'] = '[bounded flood omitted]'
    report = dict(passed=passed, tests=evidence, deployed=False, provider_calls=0)
    (Path(__file__).parent/'docs/repair-sandbox-results.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
