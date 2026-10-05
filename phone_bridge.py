"""Explicitly launched TLS-only task interface. Never imports chat/API credentials."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import secrets
import sqlite3
import ssl
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import permissions
from store import Store

ROOT = Path(__file__).resolve().parent


class Stopped(Exception):
    """The owner's emergency stop holds (permissions.py): nothing is read or changed for a phone until the
    owner resumes on the PC."""


class Bridge:
    def __init__(self, data):
        self.store = Store(data)
        with self.store.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS phone_devices (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, token_hash TEXT UNIQUE NOT NULL,
                    created REAL NOT NULL, revoked INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS phone_requests (
                    device TEXT NOT NULL, request_id TEXT NOT NULL, body_hash TEXT NOT NULL,
                    response TEXT NOT NULL, PRIMARY KEY(device, request_id));
            ''')

    def pair(self, name):
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 80:
            raise ValueError('Device name must contain 1–80 characters.')
        ident, token = uuid.uuid4().hex, secrets.token_urlsafe(32)
        with self.store.connect() as db:
            db.execute('INSERT INTO phone_devices(id,name,token_hash,created) VALUES (?,?,?,?)',
                       (ident, name.strip(), hashlib.sha256(token.encode()).hexdigest(), time.time()))
        return ident, token

    def revoke(self, ident):
        with self.store.connect() as db:
            return db.execute('UPDATE phone_devices SET revoked=1 WHERE id=?', (ident,)).rowcount == 1

    def device(self, token):
        if not isinstance(token, str) or not re.fullmatch(r'[A-Za-z0-9_-]{43}', token):
            raise PermissionError('Pair this device locally in JARVIS first.')
        with self.store.connect() as db:
            row = db.execute('SELECT id FROM phone_devices WHERE token_hash=? AND revoked=0',
                             (hashlib.sha256(token.encode()).hexdigest(),)).fetchone()
        if not row:
            raise PermissionError('Device key invalid or revoked.')
        return row['id']

    @staticmethod
    def running(db):
        # The same record the Core keeps (store.set_stop). This bridge is its own process, so it looks each time.
        if db.execute("SELECT 1 FROM control WHERE key='emergency_stop'").fetchone():
            raise Stopped()

    def tasks(self, token):
        self.device(token)
        with self.store.connect() as db:
            self.running(db)
            rows = db.execute('''SELECT i.id,i.body,i.updated,COALESCE(m.completed,0) completed
                FROM items i LEFT JOIN task_meta m ON m.item_id=i.id
                WHERE i.kind='task' ORDER BY i.updated DESC LIMIT 100''').fetchall()
        return {'tasks': [dict(row) for row in rows], 'limit': 100}

    def create(self, token, body):
        device = self.device(token)
        if not isinstance(body, dict) or set(body) != {'title', 'request_id'}:
            raise ValueError('Supply only title and request_id.')
        title, request_id = body['title'], body['request_id']
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 500:
            raise ValueError('Task title must contain 1–500 characters.')
        if not isinstance(request_id, str) or not re.fullmatch(r'[a-zA-Z0-9_-]{16,80}', request_id):
            raise ValueError('A unique request_id of 16–80 characters is required.')
        title = title.strip()
        digest = hashlib.sha256(title.encode()).hexdigest()
        with self.store.connect() as db:
            # Task and retry receipt commit together. Concurrent retries cannot duplicate work.
            db.execute('BEGIN IMMEDIATE')
            self.running(db)
            active = db.execute('SELECT revoked FROM phone_devices WHERE id=?', (device,)).fetchone()
            if not active or active['revoked']:
                raise PermissionError('Device revoked.')
            old = db.execute('SELECT * FROM phone_requests WHERE device=? AND request_id=?', (device, request_id)).fetchone()
            if old:
                if old['body_hash'] != digest:
                    raise ValueError('Request ID already used for a different task.')
                return json.loads(old['response'])
            ident, now = uuid.uuid4().hex, time.time()
            db.execute('''INSERT INTO items(id,kind,body,created,updated,category,source,confidence)
                VALUES (?, 'task', ?, ?, ?, 'task', 'phone', 1.0)''', (ident, title, now, now))
            db.execute("INSERT INTO task_meta(item_id,priority) VALUES (?,'normal')", (ident,))
            row = db.execute('SELECT id,body FROM items WHERE id=?', (ident,)).fetchone()
            result = {'status': 'saved', 'task': dict(row), 'request_id': request_id}
            db.execute('INSERT INTO phone_requests VALUES (?,?,?,?)', (device, request_id, digest, json.dumps(result)))
            db.execute('INSERT INTO audit(action,status,created,device) VALUES (?,?,?,?)', ('phone.task.create', 'saved', now, 'phone-' + device[:12]))
        return result


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def get_request(self):
        conn, addr = super().get_request()
        conn.settimeout(10)
        if self.tls is None:
            return conn, addr
        try:
            return self.tls.wrap_socket(conn, server_side=True), addr
        except Exception:
            conn.close()
            raise


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass  # Never log tokens, bodies or private task titles.

    def reply(self, status, payload, content_type='application/json'):
        data = json.dumps(payload).encode() if content_type == 'application/json' else payload
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(data)

    def handle_request(self):
        if self.headers.get('Host') != self.server.authority:
            return self.reply(403, {'error': 'Invalid host.'})
        origin = self.headers.get('Origin')
        if (origin and origin != 'https://' + self.server.authority) or self.headers.get('Sec-Fetch-Site') == 'cross-site':
            return self.reply(403, {'error': 'Cross-origin access denied.'})
        if self.command == 'GET' and self.path == '/assets/branding/teague/teague-mark.svg':
            return self.reply(200, (ROOT/'static'/'assets'/'branding'/'teague'/'teague-mark.svg').read_bytes(), 'image/svg+xml')
        if self.command == 'GET' and self.path in ('/', '/phone.js', '/phone.css'):
            name, mime = {'/': ('phone.html', 'text/html; charset=utf-8'), '/phone.js': ('phone.js', 'text/javascript'), '/phone.css': ('phone.css', 'text/css')}[self.path]
            return self.reply(200, (ROOT/'phone'/name).read_bytes(), mime)
        auth = self.headers.get('Authorization', '')
        token = auth[7:] if auth.startswith('Bearer ') else ''
        try:
            self.server.bridge.device(token)
            if self.command == 'GET' and self.path == '/v1/tasks':
                return self.reply(200, self.server.bridge.tasks(token))
            if self.command == 'POST' and self.path == '/v1/tasks':
                if self.headers.get('Transfer-Encoding') or self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                    return self.reply(400, {'error': 'Use a bounded JSON request.'})
                size = int(self.headers.get('Content-Length', '0'))
                if not 1 <= size <= 4096:
                    return self.reply(413, {'error': 'Request too large or empty.'})
                raw = self.rfile.read(size)
                if len(raw) != size:
                    raise ValueError('Incomplete request.')
                return self.reply(200, self.server.bridge.create(token, json.loads(raw)))
            return self.reply(404, {'error': 'Operation not available to phone.'})
        except Stopped:
            return self.reply(503, {'error': permissions.STOPPED_MESSAGE, 'stopped': True})
        except PermissionError:
            return self.reply(401, {'error': 'Device key invalid or revoked.'})
        except (ValueError, UnicodeError):
            return self.reply(400, {'error': 'Invalid request; verify title and unique request ID.'})
        except (sqlite3.Error, OSError):
            return self.reply(503, {'error': 'Storage unavailable. Retry using the same request ID.'})

    do_GET = handle_request
    do_POST = handle_request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=ROOT/'data')
    sub = parser.add_subparsers(dest='action', required=True)
    pair = sub.add_parser('pair')
    pair.add_argument('--name', required=True)
    pair.add_argument('--key-file', type=Path, required=True, help='New local .env-prefixed file; never print key.')
    revoke = sub.add_parser('revoke'); revoke.add_argument('id')
    sub.add_parser('devices')
    serve = sub.add_parser('serve')
    serve.add_argument('--host', default='127.0.0.1')
    serve.add_argument('--port', type=int, default=9443)
    serve.add_argument('--authority', required=True, help='Exact hostname:port used by phone')
    serve.add_argument('--cert', type=Path)
    serve.add_argument('--key', type=Path)
    serve.add_argument('--private-proxy', action='store_true', help='Loopback-only backend for Tailscale Serve HTTPS termination')
    args = parser.parse_args()
    if args.action == 'serve':
        tls = None
        if args.private_proxy:
            if args.host != '127.0.0.1':
                parser.error('Private proxy mode must bind only to 127.0.0.1.')
        else:
            if not args.cert or not args.key:
                parser.error('A TLS certificate and key are required without --private-proxy.')
            tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            tls.minimum_version = ssl.TLSVersion.TLSv1_2
            tls.load_cert_chain(args.cert, args.key)
    bridge = Bridge(args.data)
    if args.action == 'pair':
        if not args.key_file.name.startswith('.env'):
            parser.error('Use an .env-prefixed private filename excluded from backups.')
        with args.key_file.open('x', encoding='utf-8') as output:
            ident, token = bridge.pair(args.name)
            output.write(token + '\n')
        print('Device created:', ident, 'Key saved locally; not printed.')
    elif args.action == 'revoke':
        print('Revoked.' if bridge.revoke(args.id) else 'Device not found.')
    elif args.action == 'devices':
        with bridge.store.connect() as db:
            print(json.dumps([dict(r) for r in db.execute('SELECT id,name,created,revoked FROM phone_devices')]))
    else:
        server = Server((args.host, args.port), Handler)
        server.tls, server.bridge, server.authority = tls, bridge, args.authority
        print('Task bridge ready. ' + ('Loopback only; Tailscale Serve HTTPS still required.' if args.private_proxy else 'TLS enabled; phone trust and connectivity require testing.'), flush=True)
        server.serve_forever()


if __name__ == '__main__':
    main()
