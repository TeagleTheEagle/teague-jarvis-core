"""Validation-only observer; imports frozen TEST runtime without modifying it.

Parent runs two sequential disposable processes per mode. A stale TEST session
token crosses only the private parent/child pipes, never evidence or logs.
No production, live providers, Electron or implementation patches.
"""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import threading
import traceback
import uuid

OUT = Path(__file__).resolve().parent
REPO = OUT.parents[2]


def child(config):
    sys.path.insert(0, str(REPO))
    import stage4_runtime as r
    from stage4_provider_fallback import offline_router
    from stage4_deep_review import Engine, fixture_transport
    identity = r.transport.identity(os.getpid())
    mode = config['mode']
    seed = config['phase'] == 'seed'
    if seed:
        root = r.exclusion.BASE / ('TEST-STAGE4-' + uuid.uuid4().hex)
        root.mkdir()
        (root / 'TEST_ONLY').write_text('NO PRODUCTION SERVICES')
        data_id = 'TEST-' + uuid.uuid4().hex
        r.provision(root, data_id)
    else:
        root = r.validate_root(Path(config['root']))
        data_id = config['data_id']
    checks = []
    evidence = {'mode': mode, 'phase': config['phase'], 'process_identity': identity,
                'root': str(root), 'data_id': data_id, 'checks': checks,
                'scope': 'Actual TEST Context/App/Store at trusted authenticated dispatcher seam; no pipe listener or Electron',
                'simulated': True, 'paid_calls': 0}
    release = threading.Event()
    context = None
    private = None

    def check(name, ok):
        checks.append({'check': name, 'passed': bool(ok)})
        assert ok, name

    def denied(fn):
        try:
            fn()
        except (r.Denied, ValueError):
            return True
        return False

    with r.exclusion.Lock(root, 'core.lock') as lock:
        try:
            scopes = {n: r.Ownership.ORDINARY | (r.Ownership.MANAGEMENT if n == 'controller' else set())
                      for n in ('A', 'B', 'controller')}
            context = r.Context(root, data_id, lock, scopes)
            r.construct_app(context)
            context.text_router = offline_router('temporary')
            context.deep_reviewer = Engine(fixture_transport, mode='STAGE4_TEST')
            auth = r.Authority(context, {}, {n: {} for n in scopes})
            tokens = {}

            def call(owner, op, args=None, token=None):
                return auth.operation(owner, {'op': op, 'token': None if op == 'attach' else
                    tokens[owner] if token is None else token, 'args': args or {}}, 2)

            for n in scopes:
                tokens[n] = call(n, 'attach', {'scopes': sorted(scopes[n])})['token']
            family = context.owners._session(tokens['A'], context.epoch).family
            evidence.update(epoch=context.epoch, fresh_session_family=family)
            check('one App Store VoiceEngine WakeDetector', context.construction_counts ==
                  {'App': 1, 'Store': 1, 'VoiceEngine': 1, 'WakeDetector': 1})

            def submit(operation):
                if mode == 'text-only':
                    return call('A', 'request-text-only', {'text': 'Explain triangles.', 'operation': operation})
                return call('A', 'deep-review', {'review': {'mode': 'DEEP_REVIEW', 'effort': 'medium',
                    'operation': operation, 'task': 'Review E1 only.',
                    'evidence': [{'id': 'E1', 'title': 'Synthetic TEST record', 'text': 'No historical cause is established.'}]}})

            def wait(reply):
                wid = reply['request_id']
                check('worker completed within five seconds', context.owners.work[wid].done.wait(5))
                context.lifecycle.workers[wid].join(2)
                check('worker thread ended', not context.lifecycle.workers[wid].is_alive())
                return call('A', 'request-status', {'request_id': wid})

            def row(rid):
                with sqlite3.connect((context.data / 'jarvis.sqlite3').as_uri() + '?mode=ro', uri=True) as db:
                    result = db.execute('SELECT owner,session,mode,status,text,provenance FROM stage4_response_provenance WHERE response_id=?', (rid,)).fetchone()
                    count = db.execute('SELECT count(*) FROM stage4_response_provenance WHERE response_id=?', (rid,)).fetchone()[0]
                return list(result), count

            if seed:
                operation = uuid.uuid4().hex
                reply = submit(operation)
                status = wait(reply)
                rid = reply['response_id']
                committed, count = row(rid)
                provenance = call('A', 'response-provider', {'response_id': rid})
                check('explicit admitted request mode', committed[2] == mode)
                check('owner and original session persisted', committed[:2] == ['A', family])
                check('one committed answer and successful provenance', count == 1 and committed[3] == 'COMPLETED' and bool(committed[4]))
                final_events = [e for e in status['events'] if e['event'] == 'assistant.completed']
                check('one final event matches durable answer', len(final_events) == 1 and final_events[0]['data']['text'] == committed[4])
                expected = ('Ollama', 'qwen3:4b') if mode == 'text-only' else ('OpenAI', 'gpt-6-astra')
                p = provenance['provenance']
                check('actual fixture provider model and simulation label', (p['actual_final_provider'], p['actual_final_model']) == expected and p['simulated'] is True)
                check('no general tools executed', not any(e['event'].startswith('tool.') for e in status['events']))
                check('Core denies general tool execution', denied(lambda: context.check_tool('time_now', context.runs[reply['request_id']])))
                if mode == 'text-only':
                    check('simulated temporary429 fallback reason', p['fallback'] and p['fallback_reason'] == 'temporary_rate_limit')
                else:
                    check('explicit deep review routing medium effort', p['routing_reason'] == 'explicit_DEEP_REVIEW' and p['reasoning_effort'] == 'medium')
                check('foreign owner cannot inspect response', denied(lambda: call('B', 'response-provider', {'response_id': rid})))
                ack = call('A', 'cancel', {'request_id': reply['request_id']})
                check('commit-before-cancel preserves truthful completed response', ack['response_status'] == 'COMPLETED' and row(rid) == (committed, count))
                duplicate = submit(operation)
                check('duplicate operation returns same durable response', duplicate['duplicate'] and duplicate['response_id'] == rid and len(context.lifecycle.workers) == 1)

                started = threading.Event()
                if mode == 'text-only':
                    original = context.text_router.local
                    def slow(messages, model, cancel, deadline):
                        started.set()
                        if not release.wait(5):
                            raise TimeoutError('TEST generation release')
                        return original(messages, model, cancel, deadline)
                    context.text_router.local = slow  # TEST fixture transport only.
                else:
                    def slow(payload, cancel, deadline):
                        started.set()
                        if not release.wait(5):
                            raise TimeoutError('TEST generation release')
                        return fixture_transport(payload, cancel, deadline)
                    context.deep_reviewer = Engine(slow, mode='STAGE4_TEST')
                cancelled = submit(uuid.uuid4().hex)
                check('actual fixture generation entered', started.wait(3))
                ack = call('A', 'cancel', {'request_id': cancelled['request_id']})
                check('cancellation-before-commit acknowledged durably', ack['response_status'] == 'CANCELLED' and row(cancelled['response_id'])[0][3] == 'CANCELLED')
                release.set()
                cancelled_status = wait(cancelled)
                check('no final response after cancellation', not any(e['event'] == 'assistant.completed' for e in cancelled_status['events']))
                cancelled_row, _ = row(cancelled['response_id'])
                check('no cancelled answer or successful attribution', cancelled_row[4] is None and json.loads(cancelled_row[5])['actual_final_provider'] is None)
                last = call('A', 'last-response-provider')
                check('cancelled response does not displace completed query', last == provenance)
                evidence.update(operation=operation, response_id=rid, work_id=reply['request_id'],
                                persisted_row=committed, last_response=last,
                                cancelled_response_id=cancelled['response_id'])
                private = tokens['A']
            else:
                old = config['prior']
                check('new live Windows process identity', identity['created'] != old['process_identity']['created'] and
                      (identity['pid'], identity['created']) != (old['process_identity']['pid'], old['process_identity']['created']))
                check('same executable identity', identity['exe_digest'] == old['process_identity']['exe_digest'])
                check('new Core epoch and session family', context.epoch != old['epoch'] and family != old['fresh_session_family'])
                check('old token cannot authenticate', denied(lambda: call('A', 'last-response-provider', token=config['_private_token'])))
                for op in ('cancel', 'request-status'):
                    check('fresh session cannot recover old work authority: ' + op,
                          denied(lambda op=op: call('A', op, {'request_id': old['work_id']})))
                check('exact durable response survives fresh process', row(old['response_id']) == (old['persisted_row'], 1))
                last = call('A', 'last-response-provider')
                check('deterministic last provider query survives restart', last == old['last_response'])
                check('foreign owner has no completed response', call('B', 'last-response-provider')['provenance']['status'] == 'NO_COMPLETED_RESPONSE')
                check('foreign owner by-ID query denied', denied(lambda: call('B', 'response-provider', {'response_id': old['response_id']})))
                duplicate = submit(old['operation'])
                check('restart duplicate does not execute', duplicate['duplicate'] and duplicate['response_id'] == old['response_id'] and not context.lifecycle.workers and not context.text_router.records)
                cancelled, n = row(old['cancelled_response_id'])
                check('cancelled terminal state survives restart', n == 1 and cancelled[3] == 'CANCELLED' and cancelled[4] is None)
                evidence['last_response'] = last

            with sqlite3.connect((context.data / 'jarvis.sqlite3').as_uri() + '?mode=ro', uri=True) as db:
                allrows = db.execute('SELECT response_id,status,text,provenance FROM stage4_response_provenance').fetchall()
                messages = db.execute("SELECT id,content FROM messages WHERE role='assistant'").fetchall()
            check('no orphan successful provenance', all(status != 'COMPLETED' or bool(text) and json.loads(raw).get('actual_final_provider') for _, status, text, raw in allrows))
            check('no cancelled durable answer', all(status != 'CANCELLED' or text is None for _, status, text, _ in allrows))
            check('no separate orphan assistant message', messages == [])
            evidence['storage'] = {'representation': 'Existing text-only/deep-review answer text and provenance share one SQLite row; no separate messages INSERT for these modes', 'response_rows': len(allrows), 'assistant_message_rows': len(messages)}
            call('controller', 'shutdown', {'operation': uuid.uuid4().hex})
            context.lifecycle.tick()
            check('authorized lifecycle ready for clean exit', context.owners.state == 'FINALIZING')
            context.lifecycle.record_exit_ready()
            check('no live worker at exit', not any(t.is_alive() for t in context.lifecycle.workers.values()))
        except BaseException:
            evidence['failure'] = traceback.format_exc()
            private = None
        finally:
            release.set()
            if context:
                for worker in context.lifecycle.workers.values():
                    worker.join(5)
                evidence['live_workers'] = sum(t.is_alive() for t in context.lifecycle.workers.values())
    return {'public': evidence, '_private_token': private}


def parent():
    phases = []
    env = {k: v for k, v in os.environ.items() if k.upper() in ('SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA')}
    for mode in ('text-only', 'deep-review'):
        prior = None
        for phase in ('seed', 'restart'):
            cfg = {'mode': mode, 'phase': phase}
            if prior:
                cfg.update(root=prior['public']['root'], data_id=prior['public']['data_id'], prior=prior['public'], _private_token=prior['_private_token'])
            process = subprocess.Popen([sys.executable, '-B', str(Path(__file__).resolve()), '--child'], cwd=REPO,
                env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                close_fds=True, creationflags=0x08000000)
            try:
                stdout, stderr = process.communicate(json.dumps(cfg), timeout=45)
            except subprocess.TimeoutExpired:
                phases.append({'mode': mode, 'phase': phase, 'failure': 'VALIDATION_PROCESS_TIMEOUT_RETAINED', 'pid': process.pid})
                (OUT/'fresh-process-results.json').write_text(json.dumps(phases, indent=2))
                raise RuntimeError('TEST validation process retained; no automatic termination') from None
            # Never write the private envelope/raw stdout to logs.
            envelope = json.loads(stdout) if stdout else {'public': {'failure': 'NO_CHILD_RESULT'}}
            record = envelope['public']
            record.update(exit_code=process.returncode, stderr=stderr)
            phases.append(record)
            (OUT/'fresh-process-results.json').write_text(json.dumps(phases, indent=2))
            if process.returncode or record.get('failure') or record.get('live_workers'):
                print(json.dumps({'status': 'FAIL_STOP_FOR_REVIEW', 'mode': mode, 'phase': phase, 'evidence': str(OUT/'fresh-process-results.json')}))
                return 1
            prior = envelope
    print(json.dumps({'status': 'PASS', 'phases': len(phases), 'checks': sum(len(p['checks']) for p in phases), 'evidence': str(OUT/'fresh-process-results.json')}))
    return 0


if __name__ == '__main__':
    if '--child' in sys.argv:
        result = child(json.loads(sys.stdin.read()))
        sys.stdout.write(json.dumps(result))  # Private pipe consumed only by parent.
        sys.exit(1 if result['public'].get('failure') else 0)
    sys.exit(parent())
