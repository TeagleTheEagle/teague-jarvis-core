"""Stage 6 preflight/report outputs only. Never truncate finalized evidence."""
import json, os, pathlib, re

def create_bytes(path, payload):
    path = pathlib.Path(path)
    try:
        stream = path.open('xb')
    except FileExistsError as exc:
        raise FileExistsError(f'FINAL_EVIDENCE_EXISTS: {path}') from exc
    with stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    # Failure leaves the exclusive-created partial artifact, never deletes/retries it.
    return path

def create_json(path, value):
    return create_bytes(path, (json.dumps(value, indent=2, sort_keys=True)+'\n').encode('utf-8'))

def create_report(path, text):
    return create_bytes(path, text.encode('utf-8'))

def create_run(parent, run_id):
    if not re.fullmatch(r'[0-9a-f]{32}', run_id):
        raise ValueError('Explicit 32-hex run identity required')
    path = pathlib.Path(parent)/run_id
    path.mkdir(exist_ok=False)
    return path

def write_runtime(path, payload):
    """Only explicitly classified mutable state under a runtime directory."""
    path = pathlib.Path(path)
    if path.parent.name != 'runtime':
        raise ValueError('Mutable writes require explicit runtime directory')
    with path.open('wb') as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
