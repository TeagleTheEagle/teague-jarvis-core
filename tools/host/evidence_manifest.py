"""Write MANIFEST.json for Stage 6 evidence: path, size and SHA-256 of every file in the named folders.

Paths are relative to the evidence root. The sealed P0 folder is never read: it is refused by name. The
manifest does not list itself. Refuses to overwrite an existing manifest.

  python tools\\host\\evidence_manifest.py --include gate16r-20261002 guest-egress-01 --out gate16r-20261002\\MANIFEST.json
"""
import argparse
import datetime
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(r'D:\JARVIS-S6-FRESHVM\evidence')
SEALED = {'p0'}


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--root', type=Path, default=ROOT)
    ap.add_argument('--include', nargs='+', required=True, help='folders directly under the root')
    ap.add_argument('--out', type=Path, required=True, help='relative to the root')
    a = ap.parse_args()

    for name in a.include:
        if name.lower() in SEALED or Path(name).name != name or not (a.root / name).is_dir():
            sys.exit(f'STOP: {name} is sealed, not a plain folder name, or not a folder under {a.root}')
    out = a.root / a.out
    files = sorted((p for name in a.include for p in (a.root / name).rglob('*') if p.is_file() and p != out),
                   key=lambda p: p.relative_to(a.root).as_posix().lower())
    entries = [{'file': p.relative_to(a.root).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha256(p)} for p in files]
    manifest = {
        'schema': 'stage6-evidence-manifest-v1',
        'generated_utc': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'root': str(a.root), 'folders': a.include, 'not_listed': 'this manifest itself; the sealed P0 folder is never read',
        'files': len(entries), 'bytes': sum(e['bytes'] for e in entries), 'entries': entries,
    }
    try:
        with open(out, 'x', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    except FileExistsError:
        sys.exit(f'STOP: {out} already exists; not overwritten')
    print(f"{sha256(out)}  {out}  ({manifest['files']} files, {manifest['bytes']} bytes)")


if __name__ == '__main__':
    main()
