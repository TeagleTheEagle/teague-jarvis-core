"""Offline, diagnostic-only lifecycle correlation. Never supplies acceptance evidence.

Targets carry independent exact identities and conservative, independently
derived lifecycle-QPC windows in the witness clock domain. No PID-only fallback.
An absent callback never proves the identity of a lost ETW payload.
"""
import argparse
import hashlib
import json
import pathlib
import re

SCHEMA = 'stage6-lifecycle-witness-v1'
DISPOSITIONS = {'ADMITTED', 'UNKNOWN_PARENT', 'UNKNOWN_INSTANCE', 'DUPLICATE',
                'INVALID_IDENTITY', 'DECODE_FAILURE', 'OTHER_EXPLICIT_REJECTION'}
HASH = re.compile(r'[0-9a-f]{64}\Z')
ROLES = {'sampler', 'hash_worker', 'probe_1', 'probe_2', 'sampler_console',
         'hash_console', 'probe_1_console', 'probe_2_console'}

def require(ok, message):
    if not ok:
        raise ValueError(message)

def validate(w, binding):
    require(w['schema'] == SCHEMA, 'unsupported schema')
    require(w['diagnosticOnly'] is True and w['acceptanceAuthority'] is False, 'authority violation')
    for k in ('run', 'session', 'channel', 'candidateSHA256', 'observerSHA256', 'frequency'):
        require(w[k] == binding[k], 'stale/mismatched binding: ' + k)
    require(w['channel'] in ('authority', 'detailed'), 'channel')
    require(bool(w['run']) and bool(w['session']), 'empty binding')
    require(all(HASH.fullmatch(w[k]) for k in ('candidateSHA256', 'observerSHA256')), 'hash binding')
    require(type(w['frequency']) is int and w['frequency'] > 0, 'clock frequency')
    require(type(w['capacity']) is int and 0 < w['capacity'] <= 65536, 'capacity')
    require(type(w['count']) is int and 0 <= w['count'] <= w['capacity'], 'count')
    require(w['count'] == len(w['records']), 'record count')
    require(type(w['attempted']) is int and w['attempted'] >= w['count'], 'attempt count')
    require(type(w['overflow']) is bool and type(w['quiesced']) is bool, 'completion flags')
    require(w['overflow'] or w['attempted'] == w['count'], 'unreported loss')
    for i, r in enumerate(w['records'], 1):
        require(r['sequence'] == i, 'witness sequence gap/duplicate')
        require(r['kind'] in ('START', 'STOP') and r['disposition'] in DISPOSITIONS, 'record enum')
        require(r['complete'] is True, 'partial record')
        require(type(r['eventQpc']) is int and type(r['callbackQpc']) is int, 'clock fields')
        require(r['eventQpc'] > 0 and r['callbackQpc'] > 0, 'missing clock')
        require(type(r['pid']) is int and 0 <= r['pid'] <= 0xffffffff, 'pid')
        require(type(r['validFields']) is int and type(r['decodedFields']) is int
                and 0 <= r['validFields'] <= 31 and 0 <= r['decodedFields'] <= 31
                and r['validFields'] & ~r['decodedFields'] == 0, 'validity flags')
        require(type(r['admitted']) is bool and r['admitted'] == (r['disposition'] == 'ADMITTED'), 'admission contradiction')
        require(r['parentKnown'] is None or type(r['parentKnown']) is bool, 'parent decision')
        require(r['instanceKnown'] is None or type(r['instanceKnown']) is bool, 'instance decision')
        require(r['disposition'] != 'UNKNOWN_PARENT' or r['parentKnown'] is False, 'parent contradiction')
        require(r['disposition'] != 'UNKNOWN_INSTANCE' or r['instanceKnown'] is False, 'instance contradiction')
        require(r['disposition'] != 'ADMITTED' or
                (r['parentKnown'] is True if r['kind'] == 'START' else r['instanceKnown'] is True), 'missing admission decision')
    return not w['overflow'] and w['quiesced']

def targets_valid(targets, binding):
    require(targets['run'] == binding['run'] and targets['frequency'] == binding['frequency'], 'target binding')
    seen = set()
    for t in targets['instances']:
        require(type(t['pid']) is int and t['pid'] > 0, 'target PID')
        require(str(t['created']).isdigit() and int(t['created']) > 0, 'creation required: PID-only forbidden')
        require(str(t['exitFiletime']).isdigit() and int(t['exitFiletime']) >= int(t['created']), 'exit identity')
        key = (t['pid'], str(t['created']))
        require(key not in seen, 'duplicate exact instance'); seen.add(key)
        require(t['identitySource'] in ('creator-retained-handle', 'creation-verified-tracer-handle'), 'independent identity source')
        require(HASH.fullmatch(t['identityEvidenceSHA256']) is not None, 'identity evidence binding')
        for kind in ('START', 'STOP'):
            a = t['eventWindows'][kind]
            require(len(a) == 2 and all(type(x) is int and x > 0 for x in a) and a[0] <= a[1], 'independent QPC window required')
        require(t['eventWindows']['START'][0] <= t['eventWindows']['STOP'][1], 'identity interval order')

def analyze(w, binding, targets, loss):
    complete = validate(w, binding)
    targets_valid(targets, binding)
    require(loss['run'] == binding['run'] and loss['session'] == binding['session']
            and loss['frequency'] == binding['frequency'], 'loss binding')
    samples = loss['samples']
    last = None
    for s in samples:
        require(type(s['beginQpc']) is int and type(s['endQpc']) is int
                and 0 < s['beginQpc'] <= s['endQpc'], 'loss clock')
        require(type(s['eventsLost']) is int and s['eventsLost'] >= 0 and s['status'] == 0, 'loss sample invalid')
        if last:
            require(s['beginQpc'] >= last['endQpc'] and s['eventsLost'] >= last['eventsLost'], 'loss sequence')
        last = s
    result = []
    for t in targets['instances']:
        row = {'role': t['role'], 'pid': t['pid'], 'created': str(t['created'])}
        for kind in ('START', 'STOP'):
            lo, hi = t['eventWindows'][kind]
            matches, unresolved = [], []
            for r in w['records']:
                if r['kind'] != kind:
                    continue
                if not lo <= r['eventQpc'] <= hi:
                    continue
                if not r['validFields'] & 1:
                    # Callback seen in the window but PID decoding failed.
                    # It cannot be assigned, nor used to prove target absence.
                    unresolved.append(r)
                    continue
                if r['pid'] != t['pid']:
                    continue
                candidates = [v for v in targets['instances'] if v['pid'] == r['pid']
                              and v['eventWindows'][kind][0] <= r['eventQpc'] <= v['eventWindows'][kind][1]]
                if r['validFields'] & 8:
                    candidates = [v for v in candidates if v.get('processSequence') is None
                                  or str(v['processSequence']) == str(r['processSequence'])]
                # An overlapping possible reused-PID instance is never silently
                # removed when its independent sequence is unknown.
                if len(candidates) != 1 or candidates[0] is not t:
                    unresolved.append(r)
                else:
                    matches.append(r)
            if not complete:
                outcome = 'WITNESS_INCOMPLETE'
            elif unresolved or len(matches) > 1:
                outcome = 'CALLBACK_SEEN_IDENTITY_UNRESOLVED'
            elif not matches:
                outcome = 'CALLBACK_NOT_OBSERVED'
            else:
                outcome = {'ADMITTED': 'CALLBACK_ADMITTED',
                           'UNKNOWN_PARENT': 'CALLBACK_REJECTED_UNKNOWN_PARENT',
                           'UNKNOWN_INSTANCE': 'CALLBACK_REJECTED_UNKNOWN_INSTANCE'}.get(matches[0]['disposition'], 'CALLBACK_REJECTED_OTHER')
            overlap = [(a['eventsLost'], b['eventsLost']) for a, b in zip(samples, samples[1:])
                       if b['eventsLost'] > a['eventsLost'] and a['beginQpc'] <= hi and b['endQpc'] >= lo]
            row[kind] = dict(outcome=outcome, observations=matches + unresolved,
                             lossInSurroundingInterval=bool(overlap) if samples and samples[0]['beginQpc'] <= lo and samples[-1]['endQpc'] >= hi else None,
                             lossIncrements=overlap)
        result.append(row)
    return dict(schema='stage6-lifecycle-witness-analysis-v1', diagnosticOnly=True,
                acceptanceAuthority=False, run=binding['run'], channel=binding['channel'],
                complete=complete, missingRoles=sorted(ROLES - {x['role'] for x in targets['instances']}),
                instances=result, historicalCause='UNCONFIRMED',
                warning='Callback absence does not identify a lost ETW payload.')

def main():
    p = argparse.ArgumentParser()
    for x in ('witness', 'binding', 'targets', 'loss', 'output'):
        p.add_argument('--' + x, required=True, type=pathlib.Path)
    a = p.parse_args()
    load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
    inputs = {x: getattr(a, x) for x in ('witness', 'binding', 'targets', 'loss')}
    try:
        result = analyze(*(load(inputs[x]) for x in inputs))
    except (ValueError, KeyError, TypeError, OSError) as e:
        result = dict(status='WITNESS_INCOMPLETE', diagnosticOnly=True, acceptanceAuthority=False, error=str(e))
    result['inputHashes'] = {}
    for k,v in inputs.items():
        try:
            result['inputHashes'][k] = hashlib.sha256(v.read_bytes()).hexdigest()
        except OSError:
            result['inputHashes'][k] = None
    with a.output.open('x', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    return 0 if result.get('complete') and not result.get('missingRoles') else 2

if __name__ == '__main__':
    raise SystemExit(main())
