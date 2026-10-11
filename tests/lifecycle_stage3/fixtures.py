"""Synthetic TEST content over frozen, audited JARVIS schemas. No production data."""
import json
from pathlib import Path
import sqlite3
import uuid
import migration as m
import verify


def create():
    m.BASE.mkdir(exist_ok=True)
    root = m.BASE / ('TEST-' + uuid.uuid4().hex)
    root.mkdir()
    (root / 'TEST_ONLY').write_text(root.name)
    source = root / 'source'
    source.mkdir()
    for name in ('persistent', 'runtime', 'secrets', 'cache'):
        (source / name).mkdir()
    identity = {'mode': 'TEST', 'installation_id': 'TEST-installation', 'data_id': root.name}
    m.write(source / 'identity.json', identity)
    m.write(root / 'mapping.json', {'active': 'source', 'data_id': root.name})
    for name, value in {
        'personality.txt': 'SYNTHETIC TEST PERSONALITY — not JARVIS personality',
        'provider-shadow.jsonl': '{"mode":"SHADOW_ONLY","fixture":true}\n',
        'repair-evidence.json': '{"operation":"repair-1","status":"READY_FOR_REVIEW","deployed":false}',
        'device-configuration.json': '{"device":"TEST-phone","persistent_identity_only":true}',
        'evaluation.json': '{"class":"evaluation","fixture":true}',
        'client-ui.json': '{"page":"command","owner":"test-client"}',
        'recovery.json': '{"operation":"repair-1","state":"recovery_required","resume_authorized":false}',
    }.items():
        (source / 'persistent' / name).write_text(value, encoding='utf-8')
    (source / 'persistent' / 'artifact.bin').write_bytes(bytes(range(256)))
    (source / 'runtime/presence.json').write_text('{"online":true,"active_tool":true}')
    (source / 'secrets/TEST_ONLY.txt').write_text('SYNTHETIC-SECRET-SENTINEL')
    (source / 'cache/unused.txt').write_text('TEST cache')
    db = sqlite3.connect(source / 'jarvis.sqlite3')
    db.executescript((Path(__file__).parent / 'fixture.sql').read_text())
    db.execute('PRAGMA wal_autocheckpoint=0')
    db.executemany('INSERT INTO items VALUES(?,?,?,?,?,?,?,?,?)', [
        ('memory-1', 'memory', 'TEST memory Ω', 1, 2, 'fixture', 'test', 'fixture', 1),
        ('task-1', 'task', 'TEST unfinished objective', 1, 2, None, None, 'fixture', 1)])
    db.execute("INSERT INTO messages(conversation,role,content,created) VALUES('conversation-1','user','TEST conversation',1)")
    db.execute("INSERT INTO reminders VALUES('reminder-1','TEST reminder',1,0)")
    for key, value in {'provider': {'authority': 'existing', 'qwen': 'SHADOW_ONLY'},
                       'approval_history': {'approved': True, 'active_permission': False},
                       'repair_operation': {'id': 'repair-1', 'status': 'READY_FOR_REVIEW', 'deployed': False},
                       'task_plan': {'task': 'task-1', 'state': 'unfinished', 'resume_authorized': False}}.items():
        db.execute('INSERT INTO settings VALUES(?,?)', (key, json.dumps(value)))
    db.execute("INSERT INTO audit(action,status,created) VALUES('TEST approval history','recorded',1)")
    db.execute("INSERT INTO feedback(conversation,message,rating,created) VALUES('conversation-1','1','test',1)")
    db.execute("INSERT INTO documents VALUES('doc-1','TEST document','Synthetic content',1,2)")
    db.execute("INSERT INTO task_meta VALUES('task-1','high',1,NULL,0,NULL)")
    db.execute("INSERT INTO research(conversation,query,result,created) VALUES('conversation-1','TEST query','TEST result',1)")
    db.execute("INSERT INTO turn_evidence(conversation,tool,result,created) VALUES('conversation-1','TEST-tool','persistent/repair-evidence.json',1)")
    db.execute("INSERT INTO workspaces VALUES('project-1','TEST project')")
    db.execute("INSERT INTO workspace_links VALUES('project-1','task','task-1','TEST task','TEST link')")
    db.execute("INSERT INTO project_budget_limits VALUES('project-1',20,20)")
    for i, state in enumerate(('held', 'started', 'recovery_required', 'settled', 'released')):
        db.execute('INSERT INTO project_budget_reservations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                   ('project-1', 'operation-' + str(i), 'task-1', 2, 2, 1, state,
                    int(state not in ('held', 'released')), int(state in ('settled', 'started')),
                    int(state == 'settled'), 0, 2, 'succeeded' if state == 'settled' else '',
                    'persistent/repair-evidence.json' if state == 'settled' else ''))
    db.commit()
    m.write(root / 'fixture-policy.json', {'schema': verify.database(source / 'jarvis.sqlite3')['schema'],
                                         'artifacts': sorted(verify.inventory(source)['artifacts'])})
    # Kept open deliberately: latest committed pages remain in WAL during backup tests.
    return root, db
