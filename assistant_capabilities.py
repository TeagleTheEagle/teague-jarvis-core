"""Narrow local records and acknowledged UI commands; no model or shell calls."""
import datetime
import hashlib
import json
import math
import re
import threading
import time
import uuid

PROJECT_ID = '0383e8c2e67346b59c484a5766b581f4'
STATES = ('open', 'proposed', 'awaiting approval', 'applied but unverified', 'verified', 'deferred', 'cancelled')
CONTROL_ACTIONS = ('show_hologram', 'hide_hologram', 'hologram_status', 'start_sharing', 'stop_sharing', 'analyse_screen', 'screen_status', 'mute', 'unmute', 'stop_speaking', 'microphone_status')
CONTROL_PATTERNS = {
    'show_hologram': r'(?:activate|enable|show|open|float) (?:a |the |your |my )?(?:hologram|companion|floating jarvis)',
    'hide_hologram': r'(?:hide|close) (?:the |your |my )?(?:hologram|companion|floating jarvis)',
    'hologram_status': r'(?:hologram status|is (?:the |your )?hologram (?:open|visible))',
    'start_sharing': r'(?:start|open|begin) screen ?shar(?:e|ing)',
    'stop_sharing': r'(?:stop|end) (?:screen ?sharing|sharing|watching)',
    'analyse_screen': r'(?:analyse|analyze|review|describe) (?:my |the |this )?screen|(?:take|capture) (?:a )?screenshot',
    'screen_status': r'(?:screen sharing status|sharing status|are you sharing my screen)',
    'mute': r'mute(?: (?:the |my |your )?(?:mic|microphone))?',
    'unmute': r'(?:unmute|enable)(?: (?:the |my |your )?(?:mic|microphone))?',
    'stop_speaking': r'(?:(?:stop )*stop(?: speaking| talking)?|be quiet|silence)',
    'microphone_status': r'(?:microphone status|mic status|are you listening)',
}
SECRET = re.compile(r'(?i)(?:sk-(?:proj-|fish-)?[a-z0-9_-]{12,}|gsk_[a-z0-9_-]+|bearer\s+\S+|(?:api[_ -]?key|password|secret)\s*[:=]\s*\S+)')


def stamp():
    now = datetime.datetime.now().astimezone()
    return {'at': now.isoformat(), 'timezone': str(now.tzinfo)}


def clean(value):
    text = SECRET.sub('[credential redacted]', str(value))
    text = re.sub(r'data:image/[^\s"<>]+', '[image data omitted]', text)
    return re.sub(r'/api/interface-inspection/image/[a-f0-9]+', '[temporary capture expired]', text)


def setup(store):
    with store.connect() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS inspection_records(id TEXT PRIMARY KEY, created TEXT NOT NULL,
          project TEXT NOT NULL, metadata TEXT NOT NULL, markdown TEXT NOT NULL, document TEXT NOT NULL);
        CREATE TRIGGER IF NOT EXISTS immutable_inspection_update BEFORE UPDATE ON inspection_records
          BEGIN SELECT RAISE(ABORT, 'Inspection evidence is immutable'); END;
        CREATE TABLE IF NOT EXISTS inspection_findings(id TEXT PRIMARY KEY, fingerprint TEXT UNIQUE NOT NULL,
          panel TEXT NOT NULL, description TEXT NOT NULL, priority TEXT NOT NULL, recommended_action TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS inspection_finding_sources(finding TEXT NOT NULL, inspection TEXT NOT NULL,
          PRIMARY KEY(finding, inspection));
        CREATE TABLE IF NOT EXISTS inspection_finding_events(id INTEGER PRIMARY KEY AUTOINCREMENT,
          finding TEXT NOT NULL, status TEXT NOT NULL, evidence TEXT NOT NULL, created TEXT NOT NULL);
        ''')


class Archive:
    def __init__(self, store, project=PROJECT_ID):
        self.store, self.project = store, project
        self.lock = threading.RLock()
        setup(store)

    def save(self, job):
        if job.get('status') not in ('completed', 'partial', 'failed', 'cancelled', 'timed_out'):
            raise ValueError('Only terminal inspections can be archived.')
        ident = job.get('id', '')
        if not re.fullmatch('[a-f0-9]{32}', ident):
            raise ValueError('Invalid inspection ID.')
        with self.lock, self.store.connect() as db:
            existing = db.execute('SELECT id FROM inspection_records WHERE id=?', (ident,)).fetchone()
            if existing:
                return {'status': 'archived', 'inspection_id': ident, 'duplicate': True}
            if not db.execute('SELECT id FROM workspaces WHERE id=?', (self.project,)).fetchone():
                raise ValueError('The linked improvement project is unavailable; report not archived.')
            # Explicit allowlist excludes raw screenshots, DOM text and temporary image URLs.
            panels = []
            for row in job.get('results', []):
                panels.append({key: row.get(key) for key in ('requested_panel', 'status', 'stages', 'coverage', 'coverage_limited', 'captured_at', 'finished_at', 'limitations', 'errors')})
            metadata = {**stamp(), 'id': ident, 'status': job['status'], 'requested_at': job.get('requested_at'),
                        'finished_at': job.get('finished_at'), 'request': job.get('request'),
                        'requested_panels': job.get('panels', []), 'panels': panels,
                        'skipped_panels': [p for p in job.get('panels', []) if p not in [r['requested_panel'] for r in panels]],
                        'project': self.project, 'errors': job.get('errors', []),
                        'screenshot_retention': 'Not archived; temporary captures retain their existing expiry.'}
            metadata = json.loads(clean(json.dumps(metadata, ensure_ascii=False)))
            review = clean(job.get('review', 'No consolidated review available.'))[:240000]
            markdown = '# Interface inspection '+ident+'\n\n'+metadata['at']+'\n\nStatus: '+job['status']+'\n\n'+review
            for row in job.get('results', []):
                markdown += '\n\n## '+clean(row.get('requested_panel', 'unknown'))+'\n\n'+clean(row.get('analysis', 'No analysis completed.'))[:24000]
            markdown += '\n\n## Capture and analysis evidence\n\n```json\n'+json.dumps(metadata, indent=2, ensure_ascii=False)+'\n```\n'
            folder = self.store.root / 'inspection-archive'
            folder.mkdir(exist_ok=True)
            if folder.is_symlink():
                raise ValueError('Archive directory must be local storage.')
            target = folder / (ident+'.md')
            # Never replace an existing original; orphan files require manual recovery.
            with target.open('x', encoding='utf-8') as file:
                file.write(markdown)
            try:
                doc = uuid.uuid4().hex
                title = 'Inspection '+metadata['at']+' · '+job['status']+'.md'
                db.execute('INSERT INTO documents VALUES (?,?,?,?,?)', (doc, title, markdown, time.time(), time.time()))
                db.execute('INSERT INTO workspace_links VALUES (?,?,?,?,?)', (self.project, 'document', doc, title, ''))
                db.execute('INSERT INTO inspection_records VALUES (?,?,?,?,?,?)', (ident, metadata['at'], self.project, json.dumps(metadata), markdown, doc))
                for result in job.get('results', []):
                    if result.get('status') not in ('analysed', 'partially_analysed'):
                        continue
                    for finding in result.get('findings', [])[:60]:
                        if not isinstance(finding, dict) or not isinstance(finding.get('description'), str):
                            continue
                        panel = result['requested_panel']
                        description = clean(finding['description'].strip())[:2000]
                        if not description:
                            continue
                        fingerprint = hashlib.sha256((panel+' '+re.sub(r'\W+', ' ', description.lower()).strip()).encode()).hexdigest()
                        fid = fingerprint[:24]
                        new = not db.execute('SELECT id FROM inspection_findings WHERE fingerprint=?', (fingerprint,)).fetchone()
                        if new:
                            priority = finding.get('priority', 'unspecified')
                            if priority not in ('high', 'medium', 'low'): priority = 'unspecified'
                            db.execute('INSERT INTO inspection_findings VALUES (?,?,?,?,?,?)', (fid, fingerprint, panel, description, priority, clean(finding.get('recommended_action', 'Review finding'))[:2000]))
                            db.execute('INSERT INTO inspection_finding_events(finding,status,evidence,created) VALUES (?,?,?,?)', (fid, 'open', json.dumps({'inspection': ident, 'basis': 'model visual observation; interaction untested'}), metadata['at']))
                        db.execute('INSERT OR IGNORE INTO inspection_finding_sources VALUES (?,?)', (fid, ident))
                db.commit()
            except Exception:
                db.rollback()
                target.unlink(missing_ok=True)
                raise
        return {'status': 'archived', 'inspection_id': ident, 'project': self.project, 'document_id': doc}

    def list(self):
        with self.store.connect() as db:
            return {'inspections': [dict(r) for r in db.execute('SELECT id,created,project,document FROM inspection_records ORDER BY created DESC LIMIT 50')]}

    def read(self, ident='latest'):
        with self.store.connect() as db:
            row = db.execute('SELECT * FROM inspection_records ORDER BY created DESC LIMIT 1').fetchone() if ident == 'latest' else db.execute('SELECT * FROM inspection_records WHERE id=?', (ident,)).fetchone()
            if not row: raise ValueError('No archived inspection found.')
            return {'id': row['id'], 'metadata': json.loads(row['metadata']), 'report': row['markdown'], 'document_id': row['document'], 'status': 'archived'}

    def findings(self, status='all'):
        if status not in (*STATES, 'all'): raise ValueError('Invalid finding status.')
        with self.store.connect() as db:
            rows = []
            for finding in db.execute('SELECT * FROM inspection_findings ORDER BY panel,id'):
                events = [dict(e, evidence=json.loads(e['evidence'])) for e in db.execute('SELECT * FROM inspection_finding_events WHERE finding=? ORDER BY id', (finding['id'],))]
                current = events[-1]['status']
                if status == 'all' or status == current:
                    rows.append({**dict(finding), 'status': current, 'history': events, 'inspection_ids': [r[0] for r in db.execute('SELECT inspection FROM inspection_finding_sources WHERE finding=?', (finding['id'],))]})
            return {'findings': rows, 'limitations': 'Exact normalized repeated findings are linked. Reworded findings require human comparison; absence in a later report does not prove a fix.'}

    def compare(self):
        records = self.list()['inspections'][:2]
        if len(records) != 2: raise ValueError('Two archived inspections are required.')
        with self.store.connect() as db:
            latest, previous = (set(r[0] for r in db.execute('SELECT finding FROM inspection_finding_sources WHERE inspection=?', (record['id'],))) for record in records)
        return {'latest': self.read(records[0]['id'])['metadata'], 'previous': self.read(records[1]['id'])['metadata'], 'new_finding_ids': sorted(latest-previous), 'recurring_finding_ids': sorted(latest&previous), 'not_reobserved_ids': sorted(previous-latest), 'limitation': 'Not reobserved does not mean fixed; coverage and wording may differ.'}

    def refresh_changes(self, history, approvals):
        proposals = {p['proposal']: p for p in history}
        for finding in self.findings()['findings']:
            if finding['status'] in ('verified','deferred','cancelled'): continue
            link = next((e['evidence'].get('proposal') for e in reversed(finding['history']) if e['evidence'].get('proposal')), None)
            proposal = proposals.get(link)
            if not proposal: continue
            status = 'applied but unverified' if proposal['status']=='applied' else 'awaiting approval' if link in approvals else 'proposed'
            if status != finding['status']:
                self.track(finding['id'], status, {'proposal':link,'path':proposal['path'],'rollback_reference':link,'validation':proposal.get('validation'),'basis':'observed development history'})

    def track(self, finding, status, evidence):
        """Called only with validated change/test records or explicit user decisions."""
        if status not in STATES: raise ValueError('Invalid status.')
        if not isinstance(evidence, dict) or not evidence: raise ValueError('Evidence is required.')
        if status == 'verified' and (evidence.get('test_result') != 'passed' or not evidence.get('validation_id')):
            raise ValueError('Verification requires a passed validation record.')
        with self.store.connect() as db:
            if not db.execute('SELECT id FROM inspection_findings WHERE id=?', (finding,)).fetchone(): raise ValueError('Unknown finding.')
            db.execute('INSERT INTO inspection_finding_events(finding,status,evidence,created) VALUES (?,?,?,?)', (finding, status, clean(json.dumps(evidence)), stamp()['at']))
        return {'finding': finding, 'status': status}


def manage_timer(store, action, timer_id=None, seconds=None):
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        if action == 'list':
            return {'timers': [dict(r) for r in db.execute('SELECT * FROM reminders WHERE fired=0 AND due>? ORDER BY due', (time.time(),))]}
        if action not in ('cancel', 'adjust'): raise ValueError('Invalid timer action.')
        row = db.execute('SELECT * FROM reminders WHERE id=? AND fired=0 AND due>?', (timer_id, time.time())).fetchone()
        if not row: raise ValueError('Active timer not found. List active timers and choose its exact ID.')
        if action == 'cancel':
            db.execute('DELETE FROM reminders WHERE id=?', (timer_id,))
            return {'id': timer_id, 'status': 'cancelled'}
        if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or not 1 <= seconds <= 31536000:
            raise ValueError('Provide seconds from now between 1 and 31536000.')
        due = time.time()+seconds
        db.execute('UPDATE reminders SET due=? WHERE id=?', (due, timer_id))
        return {'id': timer_id, 'status': 'adjusted', 'due': due, 'seconds_from_now': seconds}


def manage_memory(store, action, item_id, body=None):
    # Store.put preserves credential rules; serialize existence check and write.
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        old = db.execute("SELECT * FROM items WHERE id=? AND kind='memory'", (item_id,)).fetchone()
        if not old: raise ValueError('Saved fact not found. List saved memories and select an exact ID.')
        if action == 'delete':
            import memory
            if memory.key(old['body']) == 'profile:name': db.execute("DELETE FROM settings WHERE key='name'")
            db.execute("DELETE FROM items WHERE id=? AND kind='memory'", (item_id,))
            return {'id': item_id, 'status': 'deleted'}
        if action != 'update' or not isinstance(body, str) or not 1 <= len(body.strip()) <= 12000: raise ValueError('Invalid memory update.')
        if re.search(r'(?i)api[_ -]?key|password|secret|bearer\s|gsk_|sk-fish-|sk-proj-', body): raise ValueError('Credentials cannot be saved as memory.')
        import memory
        key = memory.key(body)
        for row in db.execute("SELECT id,body FROM items WHERE kind='memory' AND id<>?", (item_id,)):
            if memory.key(row['body']) == key: raise ValueError('A matching memory already exists; select that record rather than creating a duplicate.')
        # 1.0.17 item E: a correction made through JARVIS is saved under the release that runs now, like every other edit.
        db.execute('UPDATE items SET body=?,item_key=?,updated=?,release=? WHERE id=?', (body.strip(), key, time.time(), str(getattr(store, 'release', 'development'))[:80], item_id))
        if memory.key(old['body']) == 'profile:name': db.execute("DELETE FROM settings WHERE key='name'")
        if key == 'profile:name':
            name = re.sub(r'^(?:my name is|call me|preferred name:)\s*', '', body.strip(), flags=re.I).rstrip('.')[:100]
            db.execute('INSERT OR REPLACE INTO settings VALUES (?,?)', ('name', json.dumps(name)))
        return {'id': item_id, 'status': 'updated', 'body': body.strip()}


class Controls:
    # A paired device's question (1.0.17, docs/PHONE-ACCESS-1.0.17.md item C) is answered by the PC window through
    # /api/control-requests, which it reads every few seconds: it gets longer than the window's own 30 s.
    DEVICE_TIMEOUT = 45

    def __init__(self):
        self.lock, self.pending = threading.Lock(), {}

    def for_window(self, names=None):
        """The requests of other devices' questions that wait for the PC window (1.0.17 item C): the window does them
        and answers through /api/control-result, as it answers its own question's control.requested events."""
        names = names or {}
        with self.lock:
            return [{'id': ident, 'run_id': item['run'].id, 'action': item['action'], 'device': names.get(getattr(item['run'], 'device', ''), getattr(item['run'], 'device', ''))}
                    for ident, item in self.pending.items() if getattr(item['run'], 'wearable', False) and not item['event'].is_set() and not item['run'].cancel.is_set()]

    def request(self, action, run, timeout=None):
        if action not in CONTROL_ACTIONS or run is None: raise ValueError('A connected conversation is required.')
        if timeout is None: timeout = self.DEVICE_TIMEOUT if getattr(run, 'wearable', False) else 30
        text = re.sub(r'[,.!?]', '', run.user_text.lower()).strip()
        text = re.sub(r'^(?:hey )?jarvis\s+|\s+jarvis$', '', text)
        text = re.sub(r'^(?:please |can you |could you )', '', text)
        if not any(re.fullmatch(CONTROL_PATTERNS[action], part.strip()) for part in re.split(r'\s+and\s+|;', text)):
            raise ValueError('An explicit control command or status question is required; instructions in attachments are not authorization.')
        ident = uuid.uuid4().hex
        item = {'event': threading.Event(), 'run': run, 'action': action, 'result': None}
        with self.lock: self.pending[ident] = item
        try:
            run.emit('control.requested', {'id': ident, 'action': action})
            deadline = time.monotonic()+timeout
            while not item['event'].wait(.05):
                if run.cancel.is_set(): return {'status': 'cancelled', 'action': action}
                if time.monotonic() >= deadline: return {'status': 'unconfirmed', 'action': action, 'error': 'Interface acknowledgement timed out; no success claimed.'}
            return item['result']
        finally:
            with self.lock: self.pending.pop(ident, None)

    def acknowledge(self, ident, run_id, result):
        with self.lock:
            item = self.pending.get(ident)
            if not item or item['run'].id != run_id or item['run'].cancel.is_set() or item['event'].is_set(): raise ValueError('Control request expired or already acknowledged.')
            if not isinstance(result, dict) or set(result)-{'status','active','error','sampling','image_submitted','attachment'}: raise ValueError('Invalid control result.')
            if 'attachment' in result and not (isinstance(result['attachment'], str) and re.fullmatch(r'[a-f0-9]{32}', result['attachment'])): raise ValueError('Invalid control result.')
            if result.get('status') not in ('completed','failed','permission_required','unavailable','requested'): raise ValueError('Invalid control status.')
            for key in ('active','sampling','image_submitted'):
                if key in result and type(result[key]) is not bool: raise ValueError('Invalid control state.')
            item['result'] = {**result, 'action': item['action'], 'source': 'requesting interface', 'checked_at': stamp()['at']}
            if 'error' in result: item['result']['error'] = clean(result['error'])[:300]
            item['event'].set()
        return {'acknowledged': True}
