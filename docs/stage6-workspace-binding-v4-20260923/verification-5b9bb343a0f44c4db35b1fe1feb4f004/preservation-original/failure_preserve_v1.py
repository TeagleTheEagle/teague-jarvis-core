"""TEST evidence preservation only. No process control, retries or acceptance API.

CLI paths are pinned by policy.json. Unknown/live writers cause a metadata-only
partial archive. Stable files are held with Windows read-only, deny-write/delete
handles until independent archive verification and the second census complete.
"""
from __future__ import annotations

import contextlib
import ctypes
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import zipfile

LABEL = 'NON-ACCEPTANCE FAILURE EVIDENCE'
RUN = re.compile(r'protected-[0-9a-f]{32}')
FAILURE_STATES = {'FAILED', 'REJECTED', 'BLOCKED', 'INCOMPLETE'}
EXPECTED = (
    'contract.json', 'small-declaration-v3.json', 'launcher-identity.json',
    'observer-identities.json', 'etw-ready.json', 'detail/etw-ready.json',
    'app-ready.json', 'integration-launcher.json', 'hash-pass-1.json',
    'hash-pass-2.json', 'metadata-verified.json', 'cleanup-origin-v3.json',
    'phase-a-v3.json', 'terminal-v3.json', 'terminal-observed-v3.json',
    'tree-handles.json', 'tree-image-support.json', 'workload-census-v3.json',
    'observer-tail-v3.json', 'observer-exits-v3.json', 'launcher-result.json',
    'app-result.json', 'detail/etw-result.json', 'etw-result.json',
    'external-exits-v3.json', 'final-census-v3.json',
)
ACCEPTANCE_OUTPUTS = {'v3-archive-receipt.json'}
STAGES = {
    'observerStartup': 'observer-identities.json',
    'collector': 'stress-result.json', 'phaseA': 'phase-a-v3.json',
    'terminalReceipt': 'terminal-v3.json', 'helperEvidence': 'tree-handles.json',
    'observerShutdown': 'observer-exits-v3.json', 'launcherExit': 'launcher-result.json',
    'finalCensus': 'final-census-v3.json', 'checker': 'v3-check-result.json',
    'normalFinalizer': 'v3-seal.json',
}


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def qpc():
    value = ctypes.c_longlong()
    if not ctypes.windll.kernel32.QueryPerformanceCounter(ctypes.byref(value)):
        raise OSError('QueryPerformanceCounter')
    return value.value


def frequency():
    value = ctypes.c_longlong()
    if not ctypes.windll.kernel32.QueryPerformanceFrequency(ctypes.byref(value)):
        raise OSError('QueryPerformanceFrequency')
    return value.value


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def encode(value):
    return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True).encode('utf-8')


def write_new(path, value):
    with Path(path).open('xb') as stream:
        stream.write(encode(value))
        stream.flush()
        os.fsync(stream.fileno())


def safe_path(path, base):
    """Reject escapes before filesystem access; never follow reparse points."""
    path, base = Path(path).absolute(), Path(base).absolute()
    if '..' in path.parts or not path.is_relative_to(base):
        raise ValueError('PATH_ESCAPE')
    for part in (path, *path.parents):
        if part.exists() or part.is_symlink():
            s = part.lstat()
            if getattr(s, 'st_file_attributes', 0) & 0x400 or part.is_symlink():
                raise ValueError('REPARSE_PATH')
        if part == part.parent:
            break
    if not path.resolve().is_relative_to(base.resolve()):
        raise ValueError('RESOLVED_ESCAPE')
    return path


def metadata(path):
    s = path.lstat()
    return dict(bytes=s.st_size, mtimeNs=s.st_mtime_ns, fileId=s.st_ino,
                volume=s.st_dev, links=s.st_nlink)


def inventory(root, allowed):
    rows, excluded = {}, []
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in list(dirs):
            p = Path(directory) / name
            try:
                safe_path(p, root)
            except (ValueError, OSError) as exc:
                dirs.remove(name)
                excluded.append(dict(path=p.relative_to(root).as_posix(), reason=str(exc)))
        for name in sorted(files):
            p = Path(directory) / name
            rel = p.relative_to(root).as_posix()
            try:
                safe_path(p, root)
                info = metadata(p)
                if info['links'] != 1 or not p.is_file():
                    raise ValueError('NONREGULAR_OR_HARDLINK')
                rows[rel] = info
                if not any(re.fullmatch(pattern, rel) for pattern in allowed):
                    excluded.append(dict(path=rel, reason='UNAPPROVED_ARTIFACT_NO_CONTENT_READ'))
            except (ValueError, OSError) as exc:
                excluded.append(dict(path=rel, reason=str(exc)))
    return dict(sorted(rows.items())), excluded


@contextlib.contextmanager
def locked_read(path):
    """GENERIC_READ + FILE_SHARE_READ only, never truncate or write source."""
    import msvcrt
    k = ctypes.WinDLL('kernel32', use_last_error=True)
    k.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32,
                             ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32,
                             ctypes.c_void_p]
    k.CreateFileW.restype = ctypes.c_void_p
    k.CloseHandle.argtypes = [ctypes.c_void_p]
    h = k.CreateFileW(str(path), 0x80000000, 1, None, 3, 0x00200000, None)
    if h == ctypes.c_void_p(-1).value:
        raise OSError(ctypes.get_last_error(), 'SOURCE_NOT_EXCLUSIVELY_READABLE')
    try:
        fd = msvcrt.open_osfhandle(h, os.O_RDONLY | os.O_BINARY)
    except BaseException:
        k.CloseHandle(h)
        raise
    with os.fdopen(fd, 'rb') as stream:
        yield stream


def parsed(data):
    try:
        return json.loads(data.decode('utf-8-sig'))
    except (UnicodeError, ValueError):
        return None


def foreign_binding(value, run):
    if not isinstance(value, dict):
        return False
    for obj in (value, value.get('binding', {})):
        if isinstance(obj, dict) and 'run' in obj:
            text = str(obj['run'])
            if text != run.name and text.replace('\\', '/').rstrip('/') != run.as_posix():
                return True
    return False


def census_clean(value, run):
    return (value.get('run') == run.name and value.get('evidenceRoot') == str(run)
            and value.get('available') is True and value.get('processes') == []
            and value.get('traces') == [] and value.get('unknown') == [])


def instance_census(objects):
    """Read-only retained handle check of recorded instances, including conhost.

    Never infer identity from PID alone. A reused PID is recorded as a different
    instance. This does not synthesize a STOP event or qualify kernel evidence.
    """
    from ctypes import wintypes as w
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
    k.GetProcessTimes.argtypes=[w.HANDLE,*([ctypes.POINTER(w.FILETIME)]*4)]
    k.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD]
    k.QueryFullProcessImageNameW.argtypes=[w.HANDLE,w.DWORD,w.LPWSTR,ctypes.POINTER(w.DWORD)]
    k.CloseHandle.argtypes=[w.HANDLE]
    identities=set();invalid=[]
    def visit(value):
        if isinstance(value,dict):
            if 'pid' in value and 'created' in value:
                try:
                    pid,created=int(value['pid']),int(value['created'])
                    if pid<=0 or created<=0:raise ValueError('NONPOSITIVE')
                    identities.add((pid,created))
                except (ValueError,TypeError):invalid.append('MALFORMED_RECORDED_IDENTITY')
            for child in value.values():visit(child)
        elif isinstance(value,list):
            for child in value:visit(child)
    for name in ('etw-result.json','detail/etw-result.json','observer-identities.json',
                 'launcher-identity.json','tree-handles.json','tree-image-support.json'):
        visit(objects.get(name))
    rows=[];unknown=list(invalid);remaining=[]
    for pid,created in sorted(identities):
        h=k.OpenProcess(0x1000|0x100000,False,pid)
        row=dict(pid=pid,expectedCreationFiletime=created)
        if not h:
            error=ctypes.get_last_error();row.update(openError=error)
            if error==87:row['state']='RECORDED_INSTANCE_ABSENT'
            else:row['state']='UNKNOWN';unknown.append(row)
            rows.append(row);continue
        try:
            values=[w.FILETIME() for _ in range(4)]
            if not k.GetProcessTimes(h,*[ctypes.byref(x) for x in values]):raise OSError('GET_PROCESS_TIMES')
            actual=(values[0].dwHighDateTime<<32)|values[0].dwLowDateTime
            row['actualCreationFiletime']=actual
            if actual!=created:row['state']='PID_REUSED_RECORDED_INSTANCE_ABSENT'
            else:
                size=w.DWORD(32768);text=ctypes.create_unicode_buffer(size.value)
                if not k.QueryFullProcessImageNameW(h,0,text,ctypes.byref(size)):raise OSError('HANDLE_IMAGE_UNAVAILABLE')
                row['actualImage']=text.value
                wait=k.WaitForSingleObject(h,0);row['waitResult']=wait
                if wait==0:row['state']='EXACT_INSTANCE_EXITED'
                elif wait==258:row['state']='EXACT_INSTANCE_STILL_LIVE';remaining.append(row)
                else:raise OSError('HANDLE_WAIT_UNCERTAIN')
        except OSError as exc:
            row.update(state='UNKNOWN',error=str(exc));unknown.append(row)
        finally:
            if not k.CloseHandle(h):unknown.append('HANDLE_CLOSE_FAILED')
        rows.append(row)
    return dict(knownInstanceCount=len(identities),rows=rows,remaining=remaining,unknown=unknown,
                clean=not remaining and not unknown,completedQpc=qpc(),completedUtc=utc())


def host_census(run):
    """Fixed read-only host census. No UAC, process termination or VM commands."""
    script = r'''
$ErrorActionPreference='Stop'
$unknown=@();$found=@()
foreach($p in @(Get-CimInstance Win32_Process)) {
 if($p.ProcessId -eq $PID -or $p.ProcessId -eq PRESERVER_PID){continue}
 if($p.Name -match '^(python|pwsh|powershell)' -and !$p.CommandLine){
  $unknown+=@{pid=$p.ProcessId;reason='COMMAND_LINE_UNAVAILABLE'};continue
 }
 if($p.Name -match '^(VBox|VirtualBox|J6)' -or ($p.Name -match '^(python|pwsh|powershell)' -and $p.CommandLine -like '*JARVIS-STAGE6-LIVE*')) {
  try {$n=Get-Process -Id $p.ProcessId -ErrorAction Stop
   $found+=@{pid=$n.Id;created=$n.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();image=$n.Path}
  } catch {$unknown+=@{pid=$p.ProcessId;reason='INSTANCE_LOOKUP_UNCERTAIN'}}
 }
}
$t=@(& logman query -ets 2>&1 | ForEach-Object{"$_"})
if($LASTEXITCODE -ne 0){throw 'TRACE_CENSUS_UNAVAILABLE'}
@{processes=@($found);unknown=@($unknown);traces=@($t|Where-Object{$_ -match '(?i)J6|JARVIS|Stage6'})}|ConvertTo-Json -Depth 6 -Compress
'''.replace('PRESERVER_PID', str(os.getpid()))
    result = dict(run=run.name, evidenceRoot=str(run), startedUtc=utc(), available=False,
                  processes=None, traces=None, unknown=['CENSUS_NOT_COMPLETED'])
    try:
        p = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script],
                           capture_output=True, text=True, timeout=10, creationflags=0x08000000)
        result.update(stdout=p.stdout, stderr=p.stderr, exitCode=p.returncode)
        if p.returncode != 0:
            raise ValueError('HOST_CENSUS_UNAVAILABLE')
        value = json.loads(p.stdout)
        if not all(isinstance(value.get(k), list) for k in ('processes', 'traces', 'unknown')):
            raise ValueError('HOST_CENSUS_SHAPE')
        result.update(value, available=True)
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        result['error'] = type(exc).__name__ + ': ' + str(exc)
    result.update(completedUtc=utc(), completedQpc=qpc(), frequency=frequency())
    return result


def verify_archive(archive, manifest_expected=None):
    """Independent reopen: exact inventory, duplicate rejection, streaming hashes."""
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        if len(names) != len(set(names)):
            raise ValueError('DUPLICATE_ARCHIVE_MEMBER')
        manifest_data = z.read('FAILURE-MANIFEST.json')
        m = json.loads(manifest_data)
        if manifest_expected is not None and manifest_data != manifest_expected:
            raise ValueError('MANIFEST_HASH_MISMATCH')
        if m['acceptance_seal'] is not False or m['label'] != LABEL or m['runOutcome'] not in FAILURE_STATES:
            raise ValueError('NON_ACCEPTANCE_MARKER')
        expected = {'FAILURE-MANIFEST.json', 'NON-ACCEPTANCE.txt'} | {'evidence/' + x['path'] for x in m['preserved']}
        if set(names) != expected:
            raise ValueError('ARCHIVE_INVENTORY_MISMATCH')
        if z.read('NON-ACCEPTANCE.txt') != (LABEL + '\n').encode():
            raise ValueError('LABEL_MISMATCH')
        for x in m['preserved']:
            with z.open('evidence/' + x['path']) as f:
                digest = hashlib.file_digest(f, 'sha256').hexdigest()
            if z.getinfo('evidence/' + x['path']).file_size != x['bytes'] or digest != x['sha256']:
                raise ValueError('ARCHIVE_HASH_MISMATCH:' + x['path'])
    return dict(verifiedArchiveMembers=len(names), archivedEvidenceFiles=len(m['preserved']),
                hashMismatches=0, missingExpectedMembers=[], archiveSHA256=sha(archive))


def preserve(run, policy, output_base, failure, census=host_census, verifier=verify_archive,
             instances=instance_census):
    """Policy and dependency injection are for offline fixtures; CLI pins both roots.

    This function does not stop or wait for writers. The launcher owns its existing
    bounded failure cleanup. If that cleanup is incomplete, no run-file content is
    copied. All preservation writes are outside the failed evidence tree.
    """
    base = Path(policy['candidate']).absolute()
    run = Path(run).absolute()
    if run.parent != base or not RUN.fullmatch(run.name):
        raise ValueError('UNAPPROVED_RUN_ROOT')
    safe_path(run, base)
    if not run.is_dir() or not any(run.iterdir()):
        raise ValueError('NOTHING_TO_PRESERVE')
    if failure.get('classification') not in FAILURE_STATES:
        raise ValueError('FAILURE_REQUIRED')
    if any((run / n).exists() for n in ACCEPTANCE_OUTPUTS):
        raise ValueError('ACCEPTANCE_ARCHIVE_PRESENT_USE_SUCCESS_PATH')
    output_base = Path(output_base).absolute()
    safe_path(output_base, output_base)
    if output_base.is_relative_to(base) or base.is_relative_to(output_base):
        raise ValueError('OUTPUT_SOURCE_OVERLAP')
    target = output_base / ('FAILURE-EVIDENCE-' + run.name)
    target.mkdir(parents=False, exist_ok=False)  # one failure archive; no retry/overwrite
    write_new(target / 'first-failure-observed.json', failure)
    archive = target / ('FAILURE-EVIDENCE-' + run.name + '.zip')
    try:
        first = census(run)
        write_new(target / 'census-before.json', first)
        before, exclusions = inventory(run, policy['artifactPatterns'])
        clean = census_clean(first, run)
        preserved, opened, objects = [], {}, {}
        with contextlib.ExitStack() as stack:
            if clean:
                excluded_names = {x['path'] for x in exclusions}
                for rel, info in before.items():
                    if rel in excluded_names:
                        continue
                    try:
                        p = safe_path(run / rel, run)
                        stream = stack.enter_context(locked_read(p))
                        if metadata(p) != info:
                            raise ValueError('SOURCE_IDENTITY_CHANGED')
                        # Small JSON metadata is interpreted only for classification/binding.
                        obj = None
                        if rel.endswith('.json') and info['bytes'] <= 1024 * 1024:
                            obj = parsed(stream.read())
                            stream.seek(0)
                        if foreign_binding(obj, run):
                            raise ValueError('CROSS_RUN_EVIDENCE_NOT_INCLUDED')
                        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
                        stream.seek(0)
                        opened[rel] = stream
                        objects[rel] = obj
                        preserved.append(dict(path=rel, **info, sha256=digest))
                    except (OSError, ValueError) as exc:
                        exclusions.append(dict(path=rel, reason=str(exc)))
                        if isinstance(exc, OSError):
                            clean = False  # a denied writer lock is not proof of quiescence
            else:
                exclusions.extend(dict(path=rel, reason='WRITER_STATE_UNPROVEN_NO_CONTENT_READ') for rel in before)
            second = census(run)
            write_new(target / 'census-after-locks.json', second)
            clean = clean and census_clean(second, run)
            exact_instances = instances(objects)
            write_new(target/'recorded-instance-census.json',exact_instances)
            clean = clean and exact_instances['clean']
            after, after_exclusions = inventory(run, policy['artifactPatterns'])
            changed = after != before
            if changed:
                exclusions.append(dict(path='*', reason='TREE_CHANGED_DURING_PRESERVATION'))
            missing = sorted(set(EXPECTED) - set(opened))
            partial = bool(missing or exclusions or changed or not clean)
            states = ['FAILURE_EVIDENCE_PARTIAL' if partial else 'FAILURE_EVIDENCE_COMPLETE']
            if not clean:
                states.insert(0, 'CLEANUP_UNPROVEN')
            origin = objects.get('cleanup-origin-v3.json') or objects.get('phase-a-v3.json')
            deadline = None
            if isinstance(origin, dict):
                freq = origin.get('frequency', (origin.get('binding') or {}).get('frequency'))
                entry = origin.get('cleanupEntryQpc')
                proposed = origin.get('deadlineQpc')
                if (type(freq) is int and freq > 0 and type(entry) is int
                        and type(proposed) is int and proposed == entry + 20*freq
                        and second.get('frequency') == freq):
                    deadline = proposed
            timely = (second['completedQpc'] < deadline) if clean and isinstance(deadline, int) else (False if not clean else None)
            observations = [dict(artifact=n, value=objects[n]) for n in (
                'primary-failure.json', 'launcher-failure.json', 'rejected-v3.json',
                'hash-failure.json', 'tail-failure-v3.json', 'terminal-failure-v3.json') if n in objects]
            timed = [o for o in observations if isinstance(o['value'], dict) and isinstance(o['value'].get('qpc'), int)]
            earliest = min(timed, key=lambda o: o['value']['qpc']) if timed else None
            decl = objects.get('small-declaration-v3.json')
            binding_problem = isinstance(decl, dict) and decl.get('sourceManifestSHA256') != policy['sourceManifestSHA256']
            if binding_problem:
                raise ValueError('DECLARATION_SOURCE_BINDING_MISMATCH')
            source_manifest = base/'small-source-v3.json'
            source_observed = sha(safe_path(source_manifest, base)) if source_manifest.is_file() else None
            manifest = dict(
                schema='stage6-failure-evidence-v1', label=LABEL, run=run.name,
                evidenceRoot=str(run), evidenceRootIdentity=metadata(run),
                sourceManifestSHA256=policy['sourceManifestSHA256'],
                observedSourceManifestSHA256=source_observed,
                sourceManifestMatchesExpected=source_observed==policy['sourceManifestSHA256'] if source_observed else None,
                fullCandidateVerification='NOT_PERFORMED_BY_FAILURE_PRESERVER',
                declarationDigest=next((x['sha256'] for x in preserved if x['path']=='small-declaration-v3.json'), None),
                knownObserverIDs=objects.get('observer-identities.json', 'UNKNOWN'),
                knownCollectorIdentity=objects.get('tree-image-support.json', 'UNKNOWN'),
                runOutcome=failure['classification'], acceptance_seal=False,
                firstFailureObserved=failure, earliestTimestampedRunFailure=earliest,
                firstAcceptanceFailureOrdering='UNCONFIRMED' if len(timed)!=len(observations) or not timed else 'EARLIEST_RECORDED_QPC',
                preservedFailureRecords=observations,
                subsequentFailures=failure.get('subsequentFailures', []),
                launchBegan=True if 'launcher-identity.json' in opened else 'UNKNOWN',
                stages={k:dict(artifact=n, state=('PRESENT_NOT_VALIDATED' if objects.get(n) is not None else 'MALFORMED_OR_NOT_PARSED') if n in opened else 'MISSING_OR_UNPRESERVED') for k,n in STAGES.items()},
                expectedArtifacts=list(EXPECTED), presentArtifacts=list(before),
                missingArtifacts=missing, existingFileCount=len(before), totalBytes=sum(x['bytes'] for x in before.values()),
                preserved=preserved, exclusions=exclusions, archiveComplete=not partial,
                potentiallyMutable=not clean or changed or any('READABLE' in x['reason'] for x in exclusions),
                cleanupProven=clean, ACCEPTANCE_CLEANUP_TIMELY=timely,
                EVENTUAL_HOST_CLEANUP_PROVEN=clean, acceptanceDeadlineQpc=deadline,
                censusBefore=first, censusAfterLocks=second, preservationStates=states,
                recordedInstanceCensus=exact_instances,
                sourceNotModifiedByTool=True, historicalCause='UNCONFIRMED',
                checkerInvoked=False, successFinalizerInvoked=False)
            manifest_data = encode(manifest)
            with (target/'FAILURE-MANIFEST.json').open('xb') as f:
                f.write(manifest_data); f.flush(); os.fsync(f.fileno())
            with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as z:
                z.writestr('NON-ACCEPTANCE.txt', LABEL+'\n')
                z.writestr('FAILURE-MANIFEST.json', manifest_data)
                for rel, stream in opened.items():
                    stream.seek(0)
                    with z.open('evidence/'+rel, 'w') as dest:
                        for data in iter(lambda:stream.read(1024*1024), b''):
                            dest.write(data)
            with archive.open('r+b') as f:
                os.fsync(f.fileno())  # output only
            verified = verifier(archive, manifest_data)
            final_inventory, _ = inventory(run, policy['artifactPatterns'])
            if final_inventory != before:
                raise ValueError('SOURCE_CHANGED_BEFORE_ARCHIVE_VERIFICATION')
            for rel, stream in opened.items():
                stream.seek(0)
                if hashlib.file_digest(stream,'sha256').hexdigest() != next(x['sha256'] for x in preserved if x['path']==rel):
                    raise ValueError('SOURCE_HASH_CHANGED')
            final_census = census(run)
            write_new(target/'census-after-archive.json', final_census)
            if clean and not census_clean(final_census, run):
                raise ValueError('CLEANUP_CHANGED_DURING_ARCHIVAL')
            final_instances=instances(objects)
            write_new(target/'recorded-instance-census-after-archive.json',final_instances)
            if clean and not final_instances['clean']:
                raise ValueError('RECORDED_INSTANCE_STATE_UNCERTAIN_AFTER_ARCHIVE')
        receipt = dict(status=states[0], states=states, label=LABEL, acceptance_seal=False,
                       runOutcome=failure['classification'], sourceEvidenceFiles=len(before),
                       manifestSHA256=sha(target/'FAILURE-MANIFEST.json'), **verified)
        write_new(target/'preservation-result.json', receipt)
        return dict(receipt, directory=str(target))
    except Exception as exc:
        result = dict(status='ARCHIVE_UNVERIFIED', label=LABEL, acceptance_seal=False,
                      runOutcome=failure['classification'], error=type(exc).__name__+': '+str(exc),
                      firstFailureObserved=failure, archiveVerified=False)
        write_new(target/'preservation-result.json', result)
        return dict(result, directory=str(target))


def cli_policy():
    p = Path(__file__).with_name('policy.json')
    value = json.loads(p.read_text())
    candidate = Path(value['candidate'])
    if candidate != Path(r'D:\JARVIS-STAGE6-LIVE\7f204e14c90a497a8476be0e9927e074\code'):
        raise ValueError('FIXED_CANDIDATE_REQUIRED')
    if Path(value['preservationRoot']) != Path(r'D:\JARVIS-STAGE6-LIVE\cab9745de28a4cae8aa6f6f7a516bf54\preservation'):
        raise ValueError('FIXED_PRESERVATION_ROOT_REQUIRED')
    return value


def verify_candidate(policy):
    base = Path(policy['candidate'])
    p = safe_path(base/'small-source-v3.json', base)
    if sha(p) != policy['sourceManifestSHA256']:
        raise ValueError('SOURCE_MANIFEST_DRIFT')
    for x in json.loads(p.read_text()):
        f = safe_path(base/x['name'], base)
        if f.stat().st_size != x['bytes'] or sha(f) != x['sha256']:
            raise ValueError('CANDIDATE_SOURCE_DRIFT:'+x['name'])


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(description=LABEL)
    parser.add_argument('run'); parser.add_argument('--component', required=True)
    parser.add_argument('--reason', required=True)
    args=parser.parse_args(); policy=cli_policy()
    if not RUN.fullmatch(args.run): raise ValueError('RUN_ID')
    failure=dict(classification='INCOMPLETE', timestampUtc=utc(), qpc=qpc(),
                 component=args.component, reason=args.reason, observationOnly=True)
    result=preserve(Path(policy['candidate'])/args.run, policy, Path(policy['preservationRoot']), failure)
    print(json.dumps(result,sort_keys=True))
