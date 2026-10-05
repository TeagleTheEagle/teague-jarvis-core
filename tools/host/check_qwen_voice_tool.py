"""Checks tools/host/Test-QwenVoice.ps1 against a stand-in for Alibaba on 127.0.0.1, with made-up keys only.
No real key is read and nothing leaves this PC. Run:  python tools/host/check_qwen_voice_tool.py
"""
import base64
import io
import json
import math
import os
import struct
import subprocess
import sys
import tempfile
import threading
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / 'Test-QwenVoice.ps1'
KEY = 'jarvis-test-' + 'k' * 24
STATE = {'voices': [], 'requests': [], 'mode': 'data', 'fail': None, 'list': None, 'total': None}


def tone(seconds, rate=24000, channels=1, bits=16):
    out = io.BytesIO()
    with wave.open(out, 'wb') as w:
        w.setnchannels(channels)
        w.setsampwidth(bits // 8)
        w.setframerate(rate)
        frames = int(seconds * rate)
        sample = lambda i: int(9000 * math.sin(i * 2 * math.pi * 220 / rate))
        if bits == 16:
            w.writeframes(b''.join(struct.pack('<h', sample(i)) * channels for i in range(frames)))
        else:
            w.writeframes(bytes((sample(i) // 256 + 128) for i in range(frames)) * channels)
    return out.getvalue()


class StandIn(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def reply(self, status, payload, kind='application/json'):
        raw = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        self.send_response(status)
        if 300 <= status < 400:
            self.send_header('Location', f'http://127.0.0.1:{self.server.server_port}/elsewhere')
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == '/sound.wav':
            STATE['requests'].append(('GET', self.path, self.headers.get('Authorization')))
            return self.reply(200, tone(1), 'audio/wav')
        self.reply(404, {})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        STATE['requests'].append(('POST', self.path, self.headers.get('Authorization'), body))
        if STATE['fail']:
            return self.reply(*STATE['fail'])
        if self.path.endswith('/services/audio/tts/customization'):
            action = body['input']['action']
            if action == 'list':
                if STATE['list'] is not None:
                    return self.reply(*STATE['list'])
                return self.reply(200, {'output': {'page_index': 0, 'page_size': 50, 'total_count': STATE['total'] or len(STATE['voices']), 'voice_list': STATE['voices']}})
            if action == 'create':
                voice = {'voice': 'qwen-tts-vc-' + body['input']['preferred_name'] + '-voice-0001', 'gmt_create': '2026-10-06 00:30:00',
                         'target_model': body['input']['target_model'], 'language': 'en'}
                STATE['voices'].append(voice)
                return self.reply(200, {'output': {'voice': voice['voice'], 'target_model': voice['target_model']}, 'usage': {'count': 1}})
        if self.path.endswith('/multimodal-generation/generation'):
            if STATE['mode'] == 'url':
                return self.reply(200, {'output': {'audio': {'url': f'http://127.0.0.1:{self.server.server_port}/sound.wav'}}})
            return self.reply(200, {'output': {'audio': {'data': base64.b64encode(tone(1)).decode()}}})
        self.reply(404, {'code': 'NotFound', 'message': 'no such route'})


def run(env_lines, *args, endpoint=True, port=None, windows_key=None):
    with tempfile.TemporaryDirectory() as folder:
        env = Path(folder) / '.env'
        env.write_text('\n'.join(env_lines) + '\n', encoding='utf-8')
        command = ['powershell', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', str(SCRIPT), '-EnvFile', str(env)]
        if endpoint:
            command += ['-TestEndpoint', f'http://127.0.0.1:{port}']
        # The real Windows variable of this account is never handed to the tool here: only a made-up one, or none.
        env = {k: v for k, v in os.environ.items() if k.upper() != 'DASHSCOPE_API_KEY'}
        env.update({'TEMP': folder, 'TMP': folder, **({'DASHSCOPE_API_KEY': windows_key} if windows_key else {})})
        done = subprocess.run(command + list(args), capture_output=True, text=True, timeout=120, env=env)
        saved = sorted(p.name for p in Path(folder).glob('jarvis-qwen-voice-test.*'))
        return done.returncode, done.stdout + done.stderr, saved


def main():
    server = ThreadingHTTPServer(('127.0.0.1', 0), StandIn)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_port
    checks = []

    def check(name, condition, output=''):
        checks.append((name, bool(condition)))
        print(('PASS  ' if condition else 'FAIL  ') + name)
        if not condition:
            print(output)

    key_line = 'DASHSCOPE_API_KEY=' + KEY
    with tempfile.TemporaryDirectory() as sounds:
        good = Path(sounds) / 'voice.wav'
        good.write_bytes(tone(12))
        # 1. An account without voices and a key file without a voice line.
        code, out, saved = run([key_line], port=port)
        check('no voice anywhere: says so and how to create one', code == 0 and 'Cloned voices on this Alibaba account: 0' in out and '-Enroll' in out and not saved, out)
        # 2. Enrol from a good recording (the stand-in mode skips the typed YES).
        code, out, _ = run([key_line], '-Enroll', str(good), port=port)
        created = [r for r in STATE['requests'] if r[0] == 'POST' and r[3]['input'].get('action') == 'create']
        check('enrol: voice created and the key-file line printed', code == 0 and 'NEW VOICE ID: qwen-tts-vc-jarvis-voice-0001' in out and 'QWEN_TTS_VOICE=qwen-tts-vc-jarvis-voice-0001' in out, out)
        check('enrol: 12.0 seconds, 24,000 Hz, mono, 16-bit read from the file', '12.0 seconds, 24,000 Hz, mono, 16-bit' in out, out)
        sent = created[-1][3]['input'] if created else {}
        check('enrol: the request is what Alibaba documents', sent.get('target_model') == 'qwen3-tts-vc-2026-01-22' and sent.get('preferred_name') == 'jarvis'
              and sent.get('audio', {}).get('data', '').startswith('data:audio/wav;base64,') and base64.b64decode(sent['audio']['data'].split(',', 1)[1]) == good.read_bytes(), str(sent)[:300])
        check('the key goes in the Authorization header only', all(r[2] == 'Bearer ' + KEY for r in STATE['requests'] if r[0] == 'POST') and KEY not in out, out)
        # 3. Recordings Alibaba would refuse are stopped before anything is sent.
        for name, data, word in (('stereo', tone(12, channels=2), 'mono'), ('16 kHz', tone(12, rate=16000), '24,000 Hz'), ('8-bit', tone(12, bits=8), '16-bit'),
                                 ('70 seconds', tone(70), '60 seconds'), ('1 second', tone(1.5), '3 seconds')):
            bad = Path(sounds) / 'bad.wav'
            bad.write_bytes(data)
            before = len(STATE['requests'])
            code, out, _ = run([key_line], '-Enroll', str(bad), port=port)
            check(f'enrol refused before sending: {name}', code == 2 and 'STOPPED' in out and word in out and len(STATE['requests']) == before, out)
        for name, args in (('no such file', ['-Enroll', str(Path(sounds) / 'none.wav')]), ('a text file', ['-Enroll', __file__]), ('a bad name', ['-Enroll', str(good), '-Name', 'my voice!'])):
            before = len(STATE['requests'])
            code, out, _ = run([key_line], *args, port=port)
            check(f'enrol refused before sending: {name}', code == 2 and 'STOPPED' in out and len(STATE['requests']) == before, out)
        # 4. List and speak with the voice in the key file (sound in the answer, then sound behind a link).
        voice_line = 'QWEN_TTS_VOICE=qwen-tts-vc-jarvis-voice-0001'
        code, out, saved = run([key_line, voice_line], port=port)
        check('speaks: lists the voice, marks it, saves a sound file', code == 0 and 'the one in your key file' in out and 'qwen voice  SPEAKS' in out and saved == ['jarvis-qwen-voice-test.wav'], out)
        spoke = [r for r in STATE['requests'] if r[0] == 'POST' and r[1].endswith('/generation')][-1][3]
        check('speaks: the request is the one JARVIS sends', spoke == {'model': 'qwen3-tts-vc-2026-01-22', 'input': {'text': 'At your service, Mr. Teague. This is the Qwen voice test.',
              'voice': 'qwen-tts-vc-jarvis-voice-0001', 'language_type': 'English'}}, str(spoke))
        STATE['mode'] = 'url'
        code, out, saved = run([key_line, voice_line], port=port)
        fetched = [r for r in STATE['requests'] if r[0] == 'GET']
        check('speaks from a link, fetched without the key', code == 0 and saved == ['jarvis-qwen-voice-test.wav'] and fetched and fetched[-1][2] is None, out)
        STATE['mode'] = 'data'
        # 5. A voice that is not on the account, and a voice made for another model.
        code, out, _ = run([key_line, 'QWEN_TTS_VOICE=someone-elses-voice'], port=port)
        check('a voice that is not on the account is said plainly', 'is NOT on this account' in out, out)
        STATE['voices'][0]['target_model'] = 'qwen3-tts-vc-realtime-2026-01-15'
        code, out, _ = run([key_line, voice_line], port=port)
        spoke = [r for r in STATE['requests'] if r[0] == 'POST' and r[1].endswith('/generation')][-1][3]
        check('a voice made for another model: says the line to add and tests with that model', 'QWEN_TTS_MODEL=qwen3-tts-vc-realtime-2026-01-15' in out and spoke['model'] == 'qwen3-tts-vc-realtime-2026-01-15', out)
        STATE['voices'][0]['target_model'] = 'qwen3-tts-vc-2026-01-22'
        # 6. Alibaba refuses: the reason is shown, an echoed key is not.
        STATE['fail'] = (403, {'code': 'AccessDenied.Unpurchased', 'message': 'Access denied for key provided: ' + KEY})
        code, out, saved = run([key_line, voice_line], port=port)
        check('a refusal shows the reason and hides an echoed key', code == 1 and 'HTTP 403' in out and 'AccessDenied.Unpurchased' in out and KEY not in out and not saved, out)
        STATE['fail'] = None
        # 6b. An answer that is not a list of voices is never read as "no voices"; a long list says it is cut.
        for name, answer in (('no list in it', (200, {'output': {}})), ('plain text', (200, b'hello', 'text/plain')), ('another shape', (200, {'voices': []}))):
            STATE['list'] = answer
            code, out, saved = run([key_line, voice_line], port=port)
            check(f'an answer that is not the list ({name}) is said to be that', code == 1 and 'COULD NOT LIST THE VOICES' in out and 'NOT on this account' not in out and 'account: 0' not in out, out)
        STATE['list'], STATE['total'] = None, 120
        code, out, _ = run([key_line, 'QWEN_TTS_VOICE=a-voice-further-down'], port=port)
        check('more voices than are listed: said, and no claim that the voice is missing', 'account: 120 (the first 1 are shown)' in out and 'not among the voices shown' in out and 'NOT on this account' not in out, out)
        STATE['total'] = None
        # 6c. A redirect answer ends the request: nothing is sent on to the address it names.
        before = len(STATE['requests'])
        STATE['fail'] = (307, {})
        code, out, saved = run([key_line, voice_line], port=port)
        check('a redirect answer ends the request', code == 1 and 'COULD NOT LIST THE VOICES' in out and len(STATE['requests']) == before + 1, out)
        STATE['fail'] = None
        # 6d. Windows holds another key than the key file: said (JARVIS uses the Windows one), neither value shown.
        other = 'jarvis-test-' + 'w' * 24
        code, out, _ = run([key_line, voice_line], port=port, windows_key=other)
        check('a different Windows variable is pointed out, without showing either key', 'DIFFERENT from the key file' in out and other not in out and KEY not in out, out)
        code, out, _ = run([key_line, voice_line], port=port, windows_key=KEY)
        check('the same key in Windows and in the file: nothing to say', 'DIFFERENT' not in out and 'qwen voice  SPEAKS' in out, out)
        code, out, _ = run([key_line], '-Enroll', str(good), '-Name', 'second', port=port, windows_key=other)
        check('creating a voice with a different Windows variable says so first', out.count('DIFFERENT from the key file') == 2 and 'NEW VOICE ID' in out, out)
        # 6e. WAV files recorders really write: a sound part whose size was never filled in, and a part named DATA.
        streamed = bytearray(tone(12))
        at = streamed.index(b'data')
        streamed[at + 4:at + 8] = (0).to_bytes(4, 'little')
        odd = Path(sounds) / 'streamed.wav'
        odd.write_bytes(bytes(streamed))
        code, out, _ = run([key_line], '-Enroll', str(odd), '-Name', 'third', port=port)
        check('a WAV whose sound size was never filled in is read to the end of the file', code == 0 and '12.0 seconds' in out, out)
        fake = tone(12)
        at = fake.index(b'data')
        fake = fake[:at] + b'DATA' + (24000 * 2 * 70).to_bytes(4, 'little') + fake[at:]  # a part named DATA ahead of the sound
        odd.write_bytes(fake[:4] + (len(fake) - 8).to_bytes(4, 'little') + fake[8:])
        before = len(STATE['requests'])
        code, out, _ = run([key_line], '-Enroll', str(odd), '-Name', 'fourth', port=port)
        check('a part named DATA is not taken for the sound', '70.0 seconds' not in out and len(STATE['requests']) == before, out)
        # 7. Guards: no key, no file, a real-looking key with the stand-in, an address that is not Alibaba's.
        before = len(STATE['requests'])
        code, out, _ = run(['OPENAI_API_KEY=x'], port=port)
        check('no Qwen key in the file: stops', code == 2 and 'no DASHSCOPE_API_KEY' in out, out)
        code, out, _ = run(['DASHSCOPE_API_KEY=sk-' + 'r' * 30], port=port)
        check('the stand-in is refused with a key that is not made up', code == 2 and 'own tests' in out and 'sk-rrr' not in out, out)
        for address in ('http://dashscope-intl.aliyuncs.com/compatible-mode/v1', 'https://example.com/compatible-mode/v1', 'https://aliyuncs.com.example.org/compatible-mode/v1', 'https://dashscope-intl.aliyuncs.com/other'):
            code, out, _ = run([key_line, 'DASHSCOPE_BASE_URL=' + address], endpoint=False)
            check(f'refused address: {address}', code == 2 and 'STOPPED' in out, out)
        code, out, _ = run([key_line, 'DASHSCOPE_TTS_URL=https://example.com/tts'], endpoint=False)
        check('refused speech address that is not Alibaba', code == 2 and 'DASHSCOPE_TTS_URL' in out, out)
        check('none of the guards sent anything', len(STATE['requests']) == before)
    server.shutdown()
    failed = [name for name, ok in checks if not ok]
    print(f'{len(checks) - len(failed)} of {len(checks)} checks passed')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
