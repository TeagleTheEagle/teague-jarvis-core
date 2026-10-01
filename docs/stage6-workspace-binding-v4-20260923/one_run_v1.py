"""Prospective one-small-run wrapper. NOT authorized to execute during this action.

The frozen driver/launcher alone owns bounded cleanup. This wrapper never retries,
terminates processes, changes deadlines, or treats preservation as acceptance.
"""
import json
from pathlib import Path
import subprocess
import sys
import failure_preserve_v1 as failure

PYTHON = r'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'


def execute(run, policy, approved=False, invoke=subprocess.run, preserve=failure.preserve):
    if not approved:
        raise ValueError('SEPARATE_ONE_RUN_AND_THREE_UAC_APPROVAL_REQUIRED')
    if not failure.RUN.fullmatch(run):
        raise ValueError('RUN_ID')
    candidate = Path(policy['candidate'])
    root = failure.safe_path(candidate/run, candidate)
    failure.verify_candidate(policy)
    if not root.is_dir():
        raise ValueError('PREPARED_RUN_REQUIRED')
    if any((root/n).exists() for n in ('launcher-identity.json', 'rejected-v3.json', 'v3-archive-receipt.json')):
        raise ValueError('RUN_ALREADY_USED_NO_RETRY')
    component = 'external_driver_v3'
    try:
        live = invoke([PYTHON, '-B', str(candidate/'external_driver_v3.py'), run,
                       '--owner-approved-one-small-run'], cwd=candidate, check=False)
        if live.returncode != 0:
            raise RuntimeError('DRIVER_EXIT_'+str(live.returncode))
        component = 'small_finalize_v3'
        final = invoke([PYTHON, '-B', '-c',
                        'import sys; from workspace import run_dir; from small_finalize_v3 import finalize; print(finalize(run_dir(sys.argv[1])))',
                        run], cwd=candidate, check=False)
        if final.returncode != 0:
            raise RuntimeError('FINALIZER_EXIT_'+str(final.returncode))
        # Finalizer owns success sealing and verification; this wrapper creates no seal.
        return dict(route='SUCCESS_FINALIZER_COMPLETED', failurePreservationInvoked=False,
                    canonicalArchiveCopyStillRequired=True)
    except Exception as exc:
        first = dict(classification='REJECTED', timestampUtc=failure.utc(), qpc=failure.qpc(),
                     component=component, reason=type(exc).__name__+': '+str(exc), observationOnly=True)
        # No wait extension. If existing cleanup is still running, preserve returns
        # CLEANUP_UNPROVEN and omits potentially live source contents.
        return preserve(root, policy, Path(policy['preservationRoot']), first)


if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[2] != '--owner-approved-one-small-run-and-three-uac':
        raise ValueError('EXPLICIT_APPROVAL_REQUIRED')
    result = execute(sys.argv[1], failure.cli_policy(), approved=True)
    print(json.dumps(result, sort_keys=True))
    sys.exit(0 if result.get('route') == 'SUCCESS_FINALIZER_COMPLETED' else 1)
