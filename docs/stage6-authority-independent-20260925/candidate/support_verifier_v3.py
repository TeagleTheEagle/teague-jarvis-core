"""TEST-only predicates. No I/O, process authority, or acceptance-checker admission.

Cross-channel inputs are a proposed fixture contract, not an adapter for real ETW.
PASS means predicates satisfied; it does not establish channel authenticity.
"""
import hashlib
from pathlib import PureWindowsPath

class Rejected(ValueError):
    pass

def require(ok, reason):
    if not ok:
        raise Rejected(reason)

def number(value):
    require(type(value) is int and value > 0, 'positive integer required')
    return value

def identity(row):
    pid = number(row['pid'])
    created = row['created']
    require(type(created) is str and created.isdecimal() and int(created) > 0,
            'creation identity required')
    return pid, created

def capture(row):
    key = identity(row)
    c = row['capture']
    require(identity(c) == key, 'capture identity mismatch')
    require(c['source'] == 'independent-tree-handle-v1', 'source mismatch')
    require((c['handlePid'], c['handleCreated']) == key and c['creationAfter'] == key[1],
            'handle identity mismatch')
    require(c['valid'] is True and c['imageError'] == 0, 'query failed')
    require(c['stateBefore'] == c['stateAfter'] == 258, 'query not proven live')
    require(type(c['handleIdentity']) is str and c['handleIdentity'].isdecimal()
            and int(c['handleIdentity']) > 0, 'handle missing')
    number(c['frequency'])
    points = [number(c[k]) for k in ('captureEntryQpc','stateBeforeQpc',
              'queryBeginQpc','queryEndQpc','stateAfterQpc')]
    require(points == sorted(points), 'timing order')
    path = PureWindowsPath(c['image'])
    require(path.is_absolute() and '..' not in path.parts and '\x00' not in c['image'],
            'invalid image path')
    require(row['closed'] is True, 'handle not closed')
    return c

def structural(doc):
    try:
        require(doc['schema'] == 'stage6-independent-tree-support-v3'
                and doc['supportingOnly'] is True
                and doc['kernelQualification'] == 'NOT_PERFORMED', 'scope changed')
        require(doc['valid'] is True and doc['errors'] == [], 'capture errors')
        anchor = doc['anchor']; capture(anchor)
        require(anchor['scopeOnly'] is True and anchor['exitFiletime'] is None
                and anchor['exitProof'] == 'EXTERNAL_NATIVE_OBSERVER_REQUIRED'
                and anchor['stateAtClose'] == 258, 'self-exit claim')
        require(number(anchor['closeQpc']) >= anchor['capture']['stateAfterQpc'], 'anchor close timing')
        rows = doc['descendants']; capacity = number(doc['capacity'])
        require(type(rows) is list and 0 < len(rows) <= capacity <= 8192, 'capacity/vacuous')
        keyed = {identity(anchor): anchor}
        for row in rows:
            key = identity(row)
            require(key not in keyed, 'duplicate identity')
            capture(row)
            require(row['capture']['frequency'] == anchor['capture']['frequency'], 'clock mismatch')
            if row['exitFiletime'] is None:
                require(row['eligibleConsoleHelper'] is True and row['parentPid']==anchor['pid'] and row['capture']['image'].lower()==r'c:\windows\system32\conhost.exe', 'unapproved pending helper')
                require(row['stateAtClose']==258 and row['exitCode'] is None, 'pending false exit')
                number(row['localCloseQpc'])
            else:
                require(type(row['exitFiletime']) is str and row['exitFiletime'].isdecimal() and int(row['exitFiletime'])>=int(key[1]), 'missing exit')
                require(type(row['exitCode']) is int, 'missing exit code')
            keyed[key] = row
        # PID by itself cannot select a parent. Require exactly one lifetime match.
        for key,row in keyed.items():
            if row is anchor: continue
            parents = [k for k,p in keyed.items() if k != key and k[0] == row['parentPid']
                       and int(k[1]) < int(key[1])
                       and (p['exitFiletime'] is None or int(key[1]) <= int(p['exitFiletime']))]
            require(len(parents) == 1, 'missing/ambiguous parent')
        return keyed
    except (KeyError, TypeError, AttributeError) as exc:
        raise Rejected('missing/malformed evidence') from exc

def cross_channel(doc, raw_sha256, binding, expected_run, kernel, independent):
    """Fixture-only boundary proposal: caller must independently prove inputs.

    No claim that sequence arrays alone prove real ETW transport completeness.
    """
    try:
        keyed = structural(doc)
        require(binding['run'] == expected_run and binding['supportSHA256'] == raw_sha256
                and len(raw_sha256) == 64, 'stale/unbound artifact')
        require(kernel['run'] == independent['run'] == expected_run, 'channel run mismatch')
        require(kernel['lost'] == 0 and kernel['complete'] is True
                and kernel['segmentsVerified'] is True, 'authority incomplete')
        require(kernel['sequence'] == list(range(1, 2*len(keyed)+1)), 'sequence gap')
        kr = kernel['rows']; ir = independent['rows']
        require(len(kr) == len(ir) == len(keyed), 'missing/extra channel identities')
        km = {identity(r): r for r in kr}; im = {identity(r): r for r in ir}
        require(len(km) == len(kr) and len(im) == len(ir)
                and set(km) == set(im) == set(keyed), 'duplicate/unmatched channel identity')
        for key,row in keyed.items():
            k=km[key]; i=im[key]; c=row['capture']
            require(k['startQpc'] <= c['captureEntryQpc'] <= c['stateAfterQpc'] < k['stopQpc'],
                    'query outside kernel lifetime')
            require(k['frequency'] == c['frequency'], 'kernel clock mismatch')
            require(i['handleSignaled'] is True and i['nativeEntryVerified'] is True,
                    'independent evidence missing')
            require(i['image'] == c['image'] and i['exitFiletime'] == k['exitFiletime'],
                    'independent contradiction')
            require(i['entryQpc'] >= k['startQpc'] and i['entryQpc'] < k['stopQpc'], 'native timing contradiction')
            if row is not doc['anchor']:
                require(k['exitFiletime'] == row['exitFiletime'], 'exit contradiction')
                parent = tuple(k['parentIdentity'])
                require(parent in keyed and parent[0] == row['parentPid']
                        and int(parent[1]) < int(key[1]), 'kernel parent contradiction')
                require(km[parent]['startQpc'] <= k['startQpc'] < km[parent]['stopQpc'], 'parent lifetime contradiction')
        return 'FIXTURE_PREDICATES_PASS_NOT_ACCEPTANCE'
    except (KeyError,TypeError,AttributeError) as exc:
        raise Rejected('missing/malformed channel evidence') from exc
