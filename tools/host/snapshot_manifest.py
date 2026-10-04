"""Write the AMENDMENT-v2 section 6(h) manifest for a Gate 16R snapshot of JARVIS-S6-FRESH.

Reads only the evidence tree: the snapshot record written by Take-FreshVmSnapshot.ps1, the .vbox copy taken
with it, and one Baseline run of Invoke-Gate17.ps1 from the guest egress folder. Embeds edition, build.UBR,
installed programs, services, PATH and the 6(f) outputs, with the snapshot UUID and the .vbox SHA-256, and
the SHA-256 of every source file. Never touches VirtualBox or the VM folder. Refuses to overwrite a manifest.

  python tools\\host\\snapshot_manifest.py --snapshot FRESH-CLEAN-BASELINE --baseline-run gate17-20261004-022130
"""
import argparse
import datetime
import hashlib
import json
import sys
from pathlib import Path

EVIDENCE = Path(r'D:\JARVIS-S6-FRESHVM\evidence\gate16r-20261002')
EGRESS = Path(r'D:\JARVIS-S6-FRESHVM\evidence\guest-egress-01')
BASELINE_FILES = ('SUMMARY.json', 'B1-baseline.json', 'baseline-programs.json', 'baseline-services.json')


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def source(path, root):
    return {'file': path.relative_to(root).as_posix(), 'bytes': path.stat().st_size, 'sha256': sha256(path)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--snapshot', required=True)
    ap.add_argument('--baseline-run', required=True, help='folder name under the guest egress folder')
    ap.add_argument('--statement', default='', help='recorded statement to carry in the manifest')
    ap.add_argument('--evidence', type=Path, default=EVIDENCE)
    ap.add_argument('--egress', type=Path, default=EGRESS)
    ap.add_argument('--out', type=Path, help='default: <evidence>\\<snapshot>-manifest.json')
    a = ap.parse_args()

    out = a.out or a.evidence / f'{a.snapshot}-manifest.json'
    records = sorted((a.evidence / 'vm').glob(f'snapshot-{a.snapshot}-*.json'))
    if len(records) != 1:
        sys.exit(f'STOP: expected one snapshot record for {a.snapshot}, found {len(records)}')
    snap = load(records[0])
    vbox_copy = a.evidence / 'vm' / f"{snap['vm_name']}.vbox.{a.snapshot}-copy"
    run = a.egress / a.baseline_run
    summary, b1, programs, services = (load(run / n) for n in BASELINE_FILES)

    problems = []
    if snap['snapshot_name'] != a.snapshot or snap['current_snapshot_uuid'] != snap['snapshot_uuid']:
        problems.append('the record does not show this snapshot as the current snapshot')
    if snap['vm_state'] != 'poweroff':
        problems.append(f"VM state in the record is {snap['vm_state']}")
    if sha256(vbox_copy) != snap['vbox_sha256_after']:
        problems.append('the .vbox copy does not match the hash in the snapshot record')
    if (summary['overall'], summary['phase'], b1['status']) != ('PASS', 'Baseline', 'PASS'):
        problems.append('the baseline run is not a passed Baseline run')
    if summary['finished_utc'] >= snap['utc']:
        problems.append('the baseline run finished after the snapshot was taken')
    if len(programs) != b1['installed_programs'] or len(services) != b1['services']:
        problems.append('program or service lists do not match the counts in B1-baseline.json')
    if problems:
        sys.exit('STOP: ' + '; '.join(problems))

    root = a.evidence.parent
    manifest = {
        'schema': 'stage6-fresh-vm-snapshot-manifest-v1',
        'requirement': 'AMENDMENT-v2 section 6(h): edition, build.UBR, installed programs, services, PATH, '
                       'the 6(f) outputs, snapshot UUID, .vbox SHA-256',
        'generated_utc': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'snapshot': {
            'name': snap['snapshot_name'], 'uuid': snap['snapshot_uuid'], 'taken_utc': snap['utc'],
            'taken_by_account': snap['account'], 'vm_name': snap['vm_name'], 'vm_uuid': snap['vm_uuid'],
            'current_snapshot_uuid': snap['current_snapshot_uuid'], 'all_snapshots': snap['all_snapshots'],
            'vm_state': snap['vm_state'],
        },
        'vbox': {
            'file': snap['vbox_file'], 'sha256': snap['vbox_sha256_after'],
            'sha256_before_snapshot': snap['before']['vbox_sha256'], 'nvram_sha256': snap['nvram_sha256_after'],
            'snapshots_folder': snap['snapshots_folder'],
        },
        'guest': {
            'edition': b1['os_caption'], 'architecture': b1['os_architecture'], 'edition_id': b1['edition_id'],
            'display_version': b1['display_version'], 'build_ubr': b1['build'],
            'activation_license_status': b1['activation_license_status'],
            'windows_update_pause_expiry': b1['windows_update_pause_expiry'], 'account': b1['account'],
        },
        'path': b1['path'],
        'installed_programs': programs,
        'services': services,
        'section_6f_outputs': b1,
        'baseline_run': {
            'folder': a.baseline_run, 'phase': summary['phase'], 'overall': summary['overall'],
            'started_utc': summary['started_utc'], 'finished_utc': summary['finished_utc'],
        },
        'sources': [source(records[0], root), source(vbox_copy, root)] + [source(run / n, root) for n in BASELINE_FILES],
    }
    if a.statement:
        manifest['statement'] = a.statement
    try:
        with open(out, 'x', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    except FileExistsError:
        sys.exit(f'STOP: {out} already exists; not overwritten')
    print(f'{sha256(out)}  {out}')


if __name__ == '__main__':
    main()
