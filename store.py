"""Small transactional local store; one connection per operation."""
import json
import sqlite3
import time
import uuid
import re
import memory
from pathlib import Path
from contextlib import contextmanager

VOICE_PROFILES = ('auto', 'fish', 'openai', 'qwen')  # the same as providers.VOICE_PROFILES


class Store:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / 'jarvis.sqlite3'
        with self.connect() as db:
            db.executescript('''
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS items (
                    id TEXT PRIMARY KEY, kind TEXT NOT NULL, body TEXT NOT NULL,
                    created REAL NOT NULL, updated REAL NOT NULL,
                    item_key TEXT, category TEXT, source TEXT, confidence REAL NOT NULL DEFAULT 1.0);
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, conversation TEXT NOT NULL,
                    role TEXT NOT NULL, content TEXT NOT NULL, created REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS reminders (
                    id TEXT PRIMARY KEY, title TEXT NOT NULL, due REAL NOT NULL,
                    fired INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL,
                    status TEXT NOT NULL, created REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, conversation TEXT, message TEXT,
                    rating TEXT NOT NULL, created REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, content TEXT NOT NULL,
                    created REAL NOT NULL, updated REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS task_meta (
                    item_id TEXT PRIMARY KEY, priority TEXT NOT NULL DEFAULT 'normal',
                    due REAL, recurrence TEXT, completed INTEGER NOT NULL DEFAULT 0,
                    completed_at REAL);
                CREATE TABLE IF NOT EXISTS research (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, conversation TEXT NOT NULL,
                    query TEXT NOT NULL, result TEXT NOT NULL, created REAL NOT NULL);
                PRAGMA user_version=1;
                CREATE TABLE IF NOT EXISTS turn_evidence (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, conversation TEXT NOT NULL,
                    tool TEXT NOT NULL, result TEXT NOT NULL, created REAL NOT NULL);
            ''')
            for column, definition in [('item_key','TEXT'),('category','TEXT'),('source','TEXT'),('confidence','REAL NOT NULL DEFAULT 1.0')]:
                try: db.execute(f'ALTER TABLE items ADD COLUMN {column} {definition}')
                except sqlite3.OperationalError: pass

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def items(self, kind):
        with self.connect() as db:
            return [dict(r) for r in db.execute('SELECT * FROM items WHERE kind=? ORDER BY updated DESC', (kind,))]

    def tasks(self, include_completed=True):
        with self.connect() as db:
            rows = [dict(r) for r in db.execute('SELECT i.*, COALESCE(m.priority,\'normal\') AS priority, m.due, m.recurrence, COALESCE(m.completed,0) AS completed, m.completed_at FROM items i LEFT JOIN task_meta m ON m.item_id=i.id WHERE i.kind=\'task\' ORDER BY completed, CASE priority WHEN \'high\' THEN 0 WHEN \'normal\' THEN 1 ELSE 2 END, due IS NULL, due, updated DESC')]
            return rows if include_completed else [r for r in rows if not r['completed']]

    def task_put(self, body, item_id=None, priority='normal', due=None, recurrence=None):
        if priority not in ('low', 'normal', 'high', 'urgent'):
            raise ValueError('Invalid task priority.')
        row = self.put('task', body, item_id)
        with self.connect() as db:
            db.execute('INSERT OR IGNORE INTO task_meta(item_id,priority,due,recurrence) VALUES (?,?,?,?)', (row['id'], priority, due, recurrence))
            db.execute('UPDATE task_meta SET priority=?,due=?,recurrence=? WHERE item_id=?', (priority, due, recurrence, row['id']))
        return next(t for t in self.tasks() if t['id'] == row['id'])

    def complete_task(self, item_id, completed=True):
        with self.connect() as db:
            row = db.execute('SELECT recurrence,due FROM task_meta WHERE item_id=?', (item_id,)).fetchone()
            if not row: db.execute('INSERT INTO task_meta(item_id,priority,completed,completed_at) VALUES (?,?,?,?)', (item_id,'normal',int(completed),time.time() if completed else None))
            else:
                db.execute('UPDATE task_meta SET completed=?,completed_at=? WHERE item_id=?', (int(completed), time.time() if completed else None, item_id))
            return True

    def put(self, kind, body, item_id=None, item_key=None, category=None, source='user', confidence=1.0):
        if kind not in ('memory', 'note', 'task', 'project'):
            raise ValueError('Unknown item type.')
        if not isinstance(body, str) or not body.strip() or len(body) > 12000:
            raise ValueError('Enter between 1 and 12,000 characters.')
        now = time.time()
        if kind == 'memory' and re.search(r'(?:api[_ -]?key|password|secret|bearer\s|gsk_|sk-fish-|sk-proj-)', body, re.I):
            raise ValueError('Credentials cannot be saved as memory.')
        with self.connect() as db:
            if kind == 'memory' and not item_id:
                rows = db.execute("SELECT id,body FROM items WHERE kind='memory'").fetchall()
                same = next((r for r in rows if memory.key(r['body']) == memory.key(body)), None)
                if same:
                    item_id = same['id']
            item_id = item_id or uuid.uuid4().hex
            existing = db.execute('SELECT kind FROM items WHERE id=?', (item_id,)).fetchone()
            if existing and existing['kind'] != kind:
                raise ValueError('Item type mismatch.')
            db.execute('INSERT INTO items(id,kind,body,created,updated,item_key,category,source,confidence) VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body, updated=excluded.updated, item_key=excluded.item_key, category=excluded.category, source=excluded.source, confidence=excluded.confidence', (item_id, kind, body.strip(), now, now, item_key or memory.key(body), category or ('project' if kind == 'project' else 'fact'), source, float(confidence)))
            if kind == 'memory' and memory.key(body) == 'profile:name':
                name = re.sub(r'^(?:my name is|call me|preferred name:)\s*', '', body.strip(), flags=re.I).rstrip('.')[:100]
                db.execute('INSERT OR REPLACE INTO settings VALUES (?,?)', ('name', json.dumps(name)))
        return {'id': item_id, 'kind': kind, 'body': body.strip()}

    def delete(self, kind, item_id):
        with self.connect() as db:
            row = db.execute('SELECT body FROM items WHERE id=? AND kind=?', (item_id, kind)).fetchone()
            if kind == 'memory' and row and memory.key(row['body']) == 'profile:name':
                db.execute("DELETE FROM settings WHERE key='name'")
            return db.execute('DELETE FROM items WHERE id=? AND kind=?', (item_id, kind)).rowcount > 0

    def message(self, conversation, role, content, *, transaction=None):
        if transaction is not None:
            # Opt-in TEST transaction participation. The caller owns commit/rollback.
            # Never open another database or silently fall back to a separate write.
            if (not isinstance(transaction, sqlite3.Connection) or not transaction.in_transaction
                    or transaction.execute('PRAGMA application_id').fetchone()[0] != 0x544934
                    or Path(transaction.execute('PRAGMA database_list').fetchone()[2]).resolve() != self.path.resolve()):
                raise ValueError('TEST_MESSAGE_TRANSACTION_REQUIRED')
            return transaction.execute('INSERT INTO messages(conversation,role,content,created) VALUES (?,?,?,?)',
                (conversation, role, content, time.time())).lastrowid
        with self.connect() as db:
            db.execute('INSERT INTO messages(conversation,role,content,created) VALUES (?,?,?,?)', (conversation, role, content, time.time()))

    def history(self, conversation, limit=100):
        with self.connect() as db:
            return [dict(r) for r in db.execute('SELECT * FROM (SELECT * FROM messages WHERE conversation=? ORDER BY id DESC LIMIT ?) ORDER BY id', (conversation, limit))]

    def record_evidence(self, conversation, tool, result):
        # Only compact public/action results; never development file contents or keys.
        allowed = {'calculate', 'create_file', 'save_item', 'set_timer', 'suit_diagram', 'project_link_chat', 'project_save_document'}
        if tool not in allowed or not isinstance(result, dict):
            return
        payload = json.dumps(result)
        if len(payload) > 6000 or re.search(r'gsk_|sk-fish-|sk-proj-|api[_ -]?key|bearer\s', payload, re.I):
            return
        with self.connect() as db:
            db.execute('INSERT INTO turn_evidence(conversation,tool,result,created) VALUES (?,?,?,?)', (conversation, tool, payload, time.time()))
            db.execute('DELETE FROM turn_evidence WHERE conversation=? AND id NOT IN (SELECT id FROM turn_evidence WHERE conversation=? ORDER BY id DESC LIMIT 8)', (conversation, conversation))

    def recent_evidence(self, conversation):
        with self.connect() as db:
            return [{'tool': r['tool'], 'result': json.loads(r['result']), 'created': r['created']} for r in db.execute('SELECT * FROM turn_evidence WHERE conversation=? ORDER BY id', (conversation,))]

    def conversations(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute("SELECT conversation AS id, MIN(created) AS created, MAX(created) AS updated, (SELECT substr(content,1,60) FROM messages m2 WHERE m2.conversation=m.conversation AND role='user' ORDER BY id LIMIT 1) AS title FROM messages m GROUP BY conversation ORDER BY updated DESC LIMIT 100")]

    def clear_conversation(self, conversation):
        with self.connect() as db:
            db.execute('DELETE FROM messages WHERE conversation=?', (conversation,))
            db.execute('DELETE FROM turn_evidence WHERE conversation=?', (conversation,))
            db.execute('DELETE FROM research WHERE conversation=?', (conversation,))

    def reminder(self, title, seconds):
        if not isinstance(title, str) or not title.strip() or len(title) > 300:
            raise ValueError('Reminder title must be 1–300 characters.')
        if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not 1 <= seconds <= 31536000:
            raise ValueError('Timer must be between one second and one year.')
        value = {'id': uuid.uuid4().hex, 'title': title, 'due': time.time() + seconds, 'fired': 0}
        with self.connect() as db:
            db.execute('INSERT INTO reminders VALUES (:id,:title,:due,:fired)', value)
        return value

    def reminders(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute('SELECT * FROM reminders ORDER BY due')]

    def due(self, now=None):
        with self.connect() as db:
            db.execute('UPDATE reminders SET fired=1 WHERE fired=0 AND due<=?', (time.time() if now is None else now,))
            return [dict(r) for r in db.execute('SELECT * FROM reminders WHERE fired=1 ORDER BY due')]

    def dismiss_reminder(self, item_id):
        with self.connect() as db:
            db.execute('DELETE FROM reminders WHERE id=?', (item_id,))

    def settings(self):
        result = {'name': '', 'voice': False, 'continuous': False, 'response_length': 'balanced', 'tone': 'cinematic', 'humor': True, 'speech_rate': 'natural', 'wake_sensitivity': 'normal', 'quiet_hours': False, 'briefing_time': '', 'proactive': False}
        with self.connect() as db:
            result.update({r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM settings')})
        if result.get('voice_profile', 'auto') not in VOICE_PROFILES:  # e.g. an ElevenLabs choice saved before 1.0.15
            result['voice_profile'] = 'auto'
        return result

    def save_settings(self, values):
        permitted = {'voice_profile': str, 'name': str, 'voice': bool, 'continuous': bool, 'response_length': str, 'tone': str, 'humor': bool, 'speech_rate': str, 'wake_sensitivity': str, 'quiet_hours': bool, 'briefing_time': str, 'proactive': bool}
        with self.connect() as db:
            for key, val in values.items():
                if key not in permitted or not isinstance(val, permitted[key]):
                    raise ValueError('Invalid setting.')
                if isinstance(val, str) and len(val) > 100:
                    raise ValueError('Setting too long.')
                if key == 'voice_profile' and val not in VOICE_PROFILES: raise ValueError('Invalid voice profile.')
                if key == 'response_length' and val not in ('brief', 'balanced', 'detailed'):
                    raise ValueError('Invalid response length.')
                if key == 'tone' and val not in ('cinematic','professional','casual'): raise ValueError('Invalid tone.')
                if key == 'speech_rate' and val not in ('slow','natural','fast'): raise ValueError('Invalid speech rate.')
                if key == 'wake_sensitivity' and val not in ('low','normal','high'): raise ValueError('Invalid wake sensitivity.')
                if key == 'briefing_time' and val and not re.fullmatch(r'([01]\d|2[0-3]):[0-5]\d', val): raise ValueError('Briefing time must use HH:MM.')
                db.execute('INSERT OR REPLACE INTO settings VALUES (?,?)', (key, json.dumps(val)))
                if key == 'name':
                    for row in db.execute("SELECT id,body FROM items WHERE kind='memory'").fetchall():
                        if memory.key(row['body']) == 'profile:name':
                            if val.strip():
                                db.execute('UPDATE items SET body=?,updated=? WHERE id=?', ('Preferred name: '+val.strip(), time.time(), row['id']))
                            else:
                                db.execute('DELETE FROM items WHERE id=?', (row['id'],))
        return self.settings()

    def audit(self, action, status):
        with self.connect() as db:
            db.execute('INSERT INTO audit(action,status,created) VALUES (?,?,?)', (action[:80], status[:80], time.time()))

    def logs(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute('SELECT * FROM audit ORDER BY id DESC LIMIT 40')]

    def feedback(self, conversation, message, rating):
        if rating not in ('helpful', 'not_helpful', 'style') or not isinstance(message, str) or len(message) > 12000:
            raise ValueError('Invalid feedback.')
        with self.connect() as db:
            db.execute('INSERT INTO feedback(conversation,message,rating,created) VALUES (?,?,?,?)', (conversation, message, rating, time.time()))
        return {'status': 'saved'}

    def save_research(self, conversation, query, result):
        with self.connect() as db:
            db.execute('INSERT INTO research(conversation,query,result,created) VALUES (?,?,?,?)', (conversation, query[:500], json.dumps(result, ensure_ascii=False)[:30000], time.time()))

    def recent_research(self, conversation, limit=3):
        with self.connect() as db:
            rows = db.execute('SELECT query,result,created FROM research WHERE conversation=? ORDER BY id DESC LIMIT ?', (conversation, limit)).fetchall()
        return [{'query': r['query'], 'result': json.loads(r['result']), 'created': r['created']} for r in rows]

    def import_data(self, payload):
        if not isinstance(payload, dict): raise ValueError('Backup must be a JSON object.')
        count = 0
        for row in payload.get('items', []):
            if row.get('kind') in ('memory','note','task','project'):
                self.put(row['kind'], row.get('body',''), row.get('id'), row.get('item_key'), row.get('category'), row.get('source','backup'), row.get('confidence',1.0)); count += 1
        with self.connect() as db:
            for row in payload.get('settings', []):
                if row.get('key') in ('name','voice','continuous','response_length'):
                    db.execute('INSERT OR REPLACE INTO settings VALUES (?,?)', (row['key'], row['value']))
        return {'status':'restored','items':count}

    def index_document(self, document_id, name, content):
        if not isinstance(name, str) or not isinstance(content, str) or len(content) > 30000:
            raise ValueError('Document is too large to index.')
        now = time.time()
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO documents VALUES (?,?,?,?,?)', (document_id, name[:250], content, now, now))
        return {'id': document_id, 'name': name[:250], 'characters': len(content)}

    def documents(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute('SELECT id,name,created,updated,length(content) AS characters FROM documents ORDER BY updated DESC')]

    def search_documents(self, query, limit=5):
        terms = [w.casefold() for w in re.findall(r'\w{3,}', query)]
        if not terms: return []
        with self.connect() as db:
            rows = [dict(r) for r in db.execute('SELECT * FROM documents')]
        scored = []
        for row in rows:
            text = row['content'].casefold(); score = sum(text.count(term) for term in terms)
            if score:
                pos = min((text.find(term) for term in terms if text.find(term) >= 0), default=0)
                start = max(0, pos - 180); end = min(len(row['content']), pos + 700)
                scored.append((score, {'id': row['id'], 'name': row['name'], 'excerpt': row['content'][start:end].strip()}))
        return [item for _, item in sorted(scored, key=lambda x: x[0], reverse=True)[:limit]]
