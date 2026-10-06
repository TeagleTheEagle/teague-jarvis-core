"""Tell the owner's JARVIS what Claude Code has finished, as a paired device of the one Core (2026-10-07, the
owner: "when you finish the task your on inform jarvis and then get jarvis to inform me when I ask him for updates").

Claude Code is a device like the phone: the owner pairs it once in Settings > Devices (name "Claude Code", kind
Computer, the tick "May save memories and tasks"), reads the code to this tool, and from then on each update is
saved into JARVIS's memory through the device route as the owner's own exact memory command ("remember that ...").
When the owner asks JARVIS for updates, JARVIS answers from its memory. Nothing else of JARVIS is touched: no
setting, no file, no other route; the live installation is reached only as a client, on 127.0.0.1.

  python tools\\host\\tell_jarvis.py pair 1234 5678         # once, with the code shown on the PC
  python tools\\host\\tell_jarvis.py say "Item A is done: ..."   # each finished task
  python tools\\host\\tell_jarvis.py status                  # is the device still paired, and what may it do

The device's own key is kept in the workspace beside the repository (claude-device.json, never in git); the Core's
port is found from the running JARVIS's listening socket on 127.0.0.1 (it changes at every start).
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_FILE = Path(__file__).resolve().parents[3] / 'claude-device.json'   # ..\JARVIS-claude-workspace\claude-device.json
NAME = 'Claude Code'
PREFIX = 'Claude Code reports: '
FIND_PORT = ("$ids = (Get-Process | Where-Object { try { $_.Path -like \"$env:LOCALAPPDATA\\JARVIS\\*\" -and $_.Name -eq 'python' } catch { $false } }).Id; "
             "Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $ids -contains $_.OwningProcess -and $_.LocalAddress -eq '127.0.0.1' } "
             "| ForEach-Object { $_.LocalPort } | Select-Object -First 1")


class Refused(Exception):
    """What the Core answered, fit to show."""


def core_url():
    """The running JARVIS's own door on this PC, from its listening socket; None when it is not running."""
    try:
        out = subprocess.run(['powershell', '-NoProfile', '-Command', FIND_PORT], capture_output=True, text=True, timeout=30).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    return f'http://127.0.0.1:{out}' if re.fullmatch(r'\d{2,5}', out) else None


def call(url, op, body, credential=None):
    data = json.dumps(body).encode()
    headers = {'Content-Type': 'application/json', 'Host': url.split('://', 1)[1]}
    if credential:
        headers['X-Jarvis-Device'] = credential
    request = urllib.request.Request(url + '/api/device/' + op, data=data, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        try:
            answer = json.load(error)
        except ValueError:
            answer = {}
        raise Refused(answer.get('error') or f'HTTP {error.code}') from None
    except (urllib.error.URLError, OSError, ValueError) as error:
        raise Refused('JARVIS could not be reached on this PC.') from None


def load(path):
    try:
        saved = json.loads(Path(path).read_text(encoding='utf-8'))
        if isinstance(saved, dict) and isinstance(saved.get('credential'), str) and isinstance(saved.get('device_id'), str):
            return saved
    except (OSError, ValueError):
        pass
    return None


def pair(url, code, path):
    paired = call(url, 'pair', {'code': code, 'capabilities': []})
    record = {'device_id': paired['device_id'], 'credential': paired['credential'], 'name': paired.get('name'), 'paired_at': time.time()}
    Path(path).write_text(json.dumps(record, indent=2), encoding='utf-8')
    return paired


def status(url, saved):
    return call(url, 'status', {}, saved['credential'])


def say(url, saved, text, wait=120):
    """One update, saved into JARVIS's memory by the owner's own exact memory command; the answer in words."""
    text = ' '.join(str(text).split())
    if not text or len(text) > 2000:
        raise Refused('Give an update of 1 to 2,000 characters.')
    conversation = 'device-' + saved['device_id'] + '-claude-code'
    started = call(url, 'start', {'text': 'remember that ' + PREFIX + text, 'conversation': conversation}, saved['credential'])
    after, deadline, answer = -1, time.time() + wait, ''
    while time.time() < deadline:
        events = call(url, 'events', {'run_id': started['run_id'], 'after': after}, saved['credential'])
        for event in events['events']:
            after = event['id']
            if event['event'] == 'assistant.completed':
                answer = event['data'].get('text') or answer
            elif event['event'] == 'run.failed':
                raise Refused('JARVIS did not save the update: ' + str(event['data'].get('error') or 'failed'))
        if events['done']:
            return answer
    raise Refused('JARVIS did not finish in time.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('action', choices=['pair', 'say', 'status'])
    parser.add_argument('words', nargs='*', help='the pairing code (pair) or the update (say)')
    parser.add_argument('--url', help="the Core's door (default: found from the running JARVIS)")
    parser.add_argument('--credential-file', default=str(DEFAULT_FILE), help='where this device keeps its own key')
    args = parser.parse_args(argv)
    url = args.url or core_url()
    try:
        if not url:
            raise Refused('JARVIS is not running on this PC (no Core listening on 127.0.0.1).')
        if args.action == 'pair':
            code = ''.join(args.words)
            if not re.fullmatch(r'\d{8}', code):
                raise Refused('The code has eight digits.')
            paired = pair(url, code, args.credential_file)
            print(f"Paired as {paired.get('name')} ({paired['device_id']}). The key is kept in {args.credential_file}.")
            print('On the PC, tick "May save memories and tasks" for it in Settings > Devices.' if not paired.get('writes') else 'It may save memories and tasks.')
            return 0
        saved = load(args.credential_file)
        if not saved:
            raise Refused(f'Not paired yet: no key in {args.credential_file}. Run: tell_jarvis.py pair <code>')
        if args.action == 'status':
            print(json.dumps(status(url, saved), indent=2))
            return 0
        current = status(url, saved)
        if not current.get('writes'):
            raise Refused('JARVIS may not save memories for this device yet: tick "May save memories and tasks" for ' + NAME + ' in Settings > Devices on the PC.')
        print(say(url, saved, ' '.join(args.words)))
        return 0
    except Refused as why:
        print(str(why), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
