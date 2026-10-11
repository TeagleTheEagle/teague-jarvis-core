"""Offline evidence validation. No launches, tracing, or cleanup mutations."""
import hashlib
import json
import zipfile
from analyzer_v1 import require, sha

def verify_archive(path, expected_hash):
    require(sha(path)==expected_hash, 'archive hash mismatch')
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        require(len(names)==len(set(names)), 'duplicate archive members')
        manifest=json.loads(z.read('archive-manifest.json'))
        entries=manifest['entries']
        require(set(names)=={'archive-manifest.json'}|{r['name'] for r in entries}, 'archive inventory mismatch')
        require(len(entries)==len({r['name'] for r in entries}), 'duplicate manifest entries')
        for row in entries:
            require(hashlib.sha256(z.read(row['name'])).hexdigest()==row['sha256'], 'archive member mismatch')
        return len(names)

def verify_census(c):
    require(c['processCount']==0 and c['traceCount']==0 and c['processes']==[] and c['traces']==[], 'cleanup not clear')
    require(c['processQuerySucceeded'] is True and c['traceQuerySucceeded'] is True, 'incomplete census')
    require(bool(c['utc']) and c['UAC'] is False, 'census provenance')
