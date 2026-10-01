"""Bounded development proposals; never execute generated code."""

import difflib

import hashlib

import json

import uuid

import time

from pathlib import Path



IMMEDIATE = ('static/pro.css', 'personality.txt')
ALLOWED = IMMEDIATE + ('static/app.js','static/voice.js','static/index.html','static/mic-worklet.js','desktop/companion.js','desktop/companion.html','desktop/companion.css','wake.py','local_stt.py','voice_engine.py','maps.py')

def read(root, path):

    if path not in ALLOWED:

        raise ValueError('Choose an allowed development source. Credentials, permissions, launchers and the action gateway are excluded.')

    target = root / path

    if target.is_symlink() or target.resolve() != root.resolve() / path:

        raise ValueError('Unsafe development target.')

    return target.read_text(encoding='utf-8')



def prepare(root, path, content, reason):

    before = read(root, path)

    if not content.strip() or len(content) > 200000:

        raise ValueError('Replacement must contain 1â€“200000 characters.')

    if path.endswith('.css') and (content.count('{') != content.count('}') or any(x in content.lower() for x in ('url(', '@import', 'expression('))):

        raise ValueError('CSS requires balanced braces and cannot load external resources.')

    validation = validate(root, path, content)

    if content == before:

        raise ValueError('No changes proposed.')

    folder = root / 'data' / 'development' / uuid.uuid4().hex

    folder.mkdir(parents=True)

    (folder/'before.txt').write_text(before,encoding='utf-8')

    (folder/'candidate.txt').write_text(content,encoding='utf-8')

    meta={'status':'staged','created':time.time(),'path':path,'reason':reason,'hash':hashlib.sha256(before.encode()).hexdigest(),'candidate_hash':hashlib.sha256(content.encode()).hexdigest(),'validation':validation}

    (folder/'meta.json').write_text(json.dumps(meta),encoding='utf-8')

    return {'proposal':folder.name,'path':path,'reason':reason,'diff':''.join(difflib.unified_diff(before.splitlines(True),content.splitlines(True),fromfile=path,tofile=path)),'validation':validation,'requires_approval':path not in IMMEDIATE}



def apply(root, proposal):

    if len(proposal)!=32 or any(x not in '0123456789abcdef' for x in proposal):

        raise ValueError('Invalid proposal.')

    folder=root/'data'/'development'/proposal

    meta=json.loads((folder/'meta.json').read_text())

    current=read(root,meta['path'])
    if meta.get('status') != 'staged':
        raise ValueError('This proposal has already been applied.')

    if hashlib.sha256(current.encode()).hexdigest()!=meta['hash']:

        raise ValueError('File changed since preview. Prepare a new proposal.')

    candidate=(folder/'candidate.txt').read_text(encoding='utf-8')

    if meta.get('candidate_hash') and hashlib.sha256(candidate.encode()).hexdigest() != meta['candidate_hash']:
        raise ValueError('Candidate changed since preview. Prepare a new proposal.')
    validation = validate(root, meta['path'], candidate)
    (root/meta['path']).write_text(candidate,encoding='utf-8')

    meta.update(status='applied', applied=time.time())

    (folder/'meta.json').write_text(json.dumps(meta),encoding='utf-8')

    return {'status':'applied','path':meta['path'],'proposal':proposal,'validation':validation,'next_step':'Restart JARVIS for Python changes; refresh for interface changes. Run the test suite and a live feature test before relying on the change.'}





def rollback(root, proposal):

    if len(proposal)!=32 or any(x not in '0123456789abcdef' for x in proposal):

        raise ValueError('Invalid proposal.')

    folder=root/'data'/'development'/proposal

    meta=json.loads((folder/'meta.json').read_text())
    if meta.get('status') != 'applied':
        raise ValueError('Only an applied change can be rolled back.')
    if read(root, meta['path']) != (folder/'candidate.txt').read_text(encoding='utf-8'):
        raise ValueError('File changed after this proposal. Read the current source and prepare a new edit.')

    return prepare(root, meta['path'], (folder/'before.txt').read_text(encoding='utf-8'), 'Restore backup '+proposal)





def history(root):

    rows=[]

    for folder in (root/'data'/'development').glob('*'):

        if not folder.is_dir() or folder.is_symlink():

            continue

        try:

            meta=json.loads((folder/'meta.json').read_text(encoding='utf-8'))

            before=(folder/'before.txt').read_text(encoding='utf-8')

            after=(folder/'candidate.txt').read_text(encoding='utf-8')

            current=read(root,meta['path'])

            rows.append({**meta,'proposal':folder.name,'created':meta.get('created',folder.stat().st_mtime),

                'status':meta.get('status','legacy — status not recorded'),

                'can_undo':current==after and before!=after,

                'diff':''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=meta['path'],tofile=meta['path'])),

                'validation':meta.get('validation','Basic content checks only. Runtime tests were not performed.')})

        except (OSError,ValueError,KeyError):

            continue

    return {'changes':sorted(rows,key=lambda r:r['created'],reverse=True)[:50]}



def validate(root, path, content):
    if path.endswith('.py'):
        import ast
        try:
            ast.parse(content)
        except SyntaxError as exc:
            raise ValueError(f'Python syntax error at line {exc.lineno}: {exc.msg}') from None
        return 'Python syntax checked without execution. Runtime behavior is untested.'
    if path.endswith('.js'):
        import subprocess, tempfile, os
        executable = root/'desktop/node_modules/electron/dist/electron.exe'
        if not executable.is_file():
            raise ValueError('The installed JavaScript checker is unavailable.')
        with tempfile.TemporaryDirectory(prefix='jarvis-syntax-') as folder:
            candidate=Path(folder)/'candidate.js'
            candidate.write_text(content,encoding='utf-8')
            result=subprocess.run([str(executable),'--check',str(candidate)],capture_output=True,text=True,timeout=15,env={**os.environ,'ELECTRON_RUN_AS_NODE':'1'},creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        if result.returncode:
            raise ValueError('JavaScript syntax check failed. '+result.stderr[-1500:])
        return 'JavaScript syntax checked without execution. Runtime behavior is untested.'
    return 'Basic content checks only. Rendering and behavior need a live test.'


def edit(root,path,old,new,reason):
    before=read(root,path)
    if not old or before.count(old)!=1:
        raise ValueError('The exact original text must match once. Read the source again.')
    return prepare(root,path,before.replace(old,new,1),reason)
