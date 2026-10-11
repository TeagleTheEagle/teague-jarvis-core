"""Provenance in the existing canonical TEST database, never production Store."""
import hashlib
import json
import sqlite3
import time
import uuid


class History:
    def __init__(self, database):
        self.database = database
        with self.connect() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS stage4_response_provenance(
                response_id TEXT PRIMARY KEY, owner TEXT NOT NULL, session TEXT NOT NULL,
                operation TEXT NOT NULL, fingerprint TEXT NOT NULL, mode TEXT NOT NULL,
                status TEXT NOT NULL, timestamp REAL NOT NULL, text TEXT,
                provenance TEXT, UNIQUE(owner,operation))''')

    def connect(self, timeout=1):
        db = sqlite3.connect(self.database.as_uri()+'?mode=rw',uri=True,timeout=min(1,max(0,timeout)))
        if db.execute('PRAGMA application_id').fetchone()[0] != 0x544934:
            db.close()
            raise ValueError('TEST_DATABASE_REQUIRED')
        return db

    def reserve(self, owner, session, operation, text, mode):
        fingerprint = hashlib.sha256((mode+'\0'+text).encode()).hexdigest()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT response_id,fingerprint FROM stage4_response_provenance WHERE owner=? AND operation=?',(owner,operation)).fetchone()
            if row:
                if row[1]!=fingerprint: raise ValueError('IDEMPOTENCY_CONFLICT')
                return row[0],False
            response_id=uuid.uuid4().hex
            db.execute('INSERT INTO stage4_response_provenance VALUES(?,?,?,?,?,?,?,?,?,?)',
                       (response_id,owner,session,operation,fingerprint,mode,'PENDING',time.time(),None,None))
            return response_id,True

    def finish(self, owner, response_id, status, text, provenance, *, session=None,
               validate=None, append=None, timeout=1):
        if status not in ('COMPLETED','FAILED','CANCELLED'): raise ValueError('STATUS')
        # One SQLite writer transaction decides cancellation versus completion.
        # The optional Store INSERT is in THIS transaction, never a nested commit.
        db=self.connect(timeout)
        try:
            with db:
                db.execute('BEGIN IMMEDIATE')
                row=db.execute('SELECT session,status,text,provenance FROM stage4_response_provenance WHERE response_id=? AND owner=?',
                    (response_id,owner)).fetchone()
                if row is None or session is not None and row[0]!=session:
                    raise ValueError('RESPONSE_NOT_OWNED')
                if row[1]!='PENDING':
                    return {'status':row[1],'text':row[2],'provenance':json.loads(row[3] or '{}'),'changed':False}
                if validate is not None and not validate():
                    status='CANCELLED'
                final=dict(provenance)
                if status!='COMPLETED':
                    text=None
                    final.update(actual_final_provider=None,actual_final_model=None)
                elif append is not None:
                    final['message_id']=append(db)
                count=db.execute('UPDATE stage4_response_provenance SET status=?,timestamp=?,text=?,provenance=? WHERE response_id=? AND owner=? AND session=? AND status=?',
                    (status,time.time(),text,json.dumps(final),response_id,owner,row[0],'PENDING')).rowcount
                if count!=1: raise ValueError('RESPONSE_ALREADY_FINAL_OR_NOT_OWNED')
                result={'status':status,'text':text,'provenance':final,'changed':True}
            # Success is visible only after the context manager COMMIT succeeds.
            return result
        finally:
            db.close()

    def last(self, owner):
        with self.connect() as db:
            row=db.execute("SELECT response_id,session,timestamp,mode,status,provenance FROM stage4_response_provenance WHERE owner=? AND status='COMPLETED' ORDER BY timestamp DESC,rowid DESC LIMIT 1",(owner,)).fetchone()
        if not row: return {'status':'NO_COMPLETED_RESPONSE'}
        rid,session,stamp,mode,status,raw=row
        return dict(response_id=rid,owner=owner,session=session,timestamp=stamp,
                    request_mode=mode,final_status=status,**json.loads(raw))

    def status(self, owner, response_id):
        with self.connect() as db:
            row=db.execute('SELECT status FROM stage4_response_provenance WHERE owner=? AND response_id=?',(owner,response_id)).fetchone()
        if not row: raise ValueError('RESPONSE_NOT_OWNED')
        return row[0]

    def get(self, owner, response_id):
        # Query binds the authenticated owner; no schema or production Store change.
        if not isinstance(response_id,str) or len(response_id)!=32 or any(c not in '0123456789abcdef' for c in response_id):
            raise ValueError('RESPONSE_ID')
        with self.connect() as db:
            row=db.execute('SELECT session,timestamp,mode,status,provenance FROM stage4_response_provenance WHERE owner=? AND response_id=?',(owner,response_id)).fetchone()
        if not row:raise ValueError('RESPONSE_NOT_OWNED')
        session,stamp,mode,status,raw=row
        return dict(response_id=response_id,owner=owner,session=session,timestamp=stamp,
                    request_mode=mode,final_status=status,**json.loads(raw or '{}'))


def describe(record):
    if record.get('final_status')!='COMPLETED': return 'No completed response is recorded for this owner.'
    provider=record.get('actual_final_provider')
    model=record.get('actual_final_model')
    prefix='TEST simulation: ' if record.get('simulated') else ''
    return prefix+f"Your last completed response was generated by {provider}; model: {model or 'not applicable'}. Fallback: {'yes' if record.get('fallback') else 'no'}."
