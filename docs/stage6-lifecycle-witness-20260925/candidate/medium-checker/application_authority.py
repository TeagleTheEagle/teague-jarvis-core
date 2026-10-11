"""Authoritative application evidence verifier. The bounded tap is never input."""
import pathlib,json,hashlib
def records(root):
 root=pathlib.Path(root);m=json.loads((root/'app-authority.json').read_text())
 if m['format']!='application-authority-v1' or m['fault'] or not m['writerExited'] or m['remaining']:raise ValueError('AUTHORITATIVE_FAILURE')
 if not m['attempted']==m['accepted']==m['persisted']:raise ValueError('ADMISSION_LOSS')
 segments=m['segments'];expected=1;total=0
 names=[f'app-authority-{n:05d}.jsonl' for n in range(len(segments))]
 if [x['name'] for x in segments]!=names or {p.name for p in root.glob('app-authority-*.jsonl')}!=set(names):raise ValueError('SEGMENT_SET')
 if len(segments)>16384:raise ValueError('SEGMENT_BOUND')
 for number,x in enumerate(segments):
  if x['number']!=number or x['first']!=expected:raise ValueError('SEGMENT_ORDER')
  p=root/x['name'];s=p.lstat()
  if s.st_file_attributes&0x400 or s.st_nlink!=1 or s.st_size!=x['bytes'] or s.st_size>8388608:raise ValueError('SEGMENT_PATH_SIZE')
  h=hashlib.sha256();count=0;size=0
  with p.open('rb') as f:
   for line in f:
    if len(line)>8192 or not line.endswith(b'\n'):raise ValueError('PARTIAL_OR_OVERSIZED_RECORD')
    h.update(line);size+=len(line);r=json.loads(line)
    if r['seq']!=expected or r['segment']!=number or not r['serialized']:raise ValueError('SEQUENCE_GAP_DUPLICATE')
    expected+=1;count+=1;yield r
  if h.hexdigest()!=x['sha256'] or count!=x['records'] or size!=x['bytes'] or expected-1!=x['last']:raise ValueError('SEGMENT_HASH_OR_COUNT')
  total+=size
 if expected-1!=m['persisted'] or total!=m['bytes'] or m['first']!=(1 if expected>1 else 0) or m['last']!=expected-1:raise ValueError('AUTHORITATIVE_TOTAL')
 if m['peakQueueBytes']>m['memoryBound'] or m['peakQueueItems']>m['itemBound'] or total>m['storageBound'] or expected-1>m['recordBound']:raise ValueError('BOUND_EXCEEDED')
def verify(root):
 count=sum(1 for _ in records(root));m=json.loads((pathlib.Path(root)/'app-authority.json').read_text());return dict(records=count,segments=len(m['segments']),sequenceGaps=0,bytes=m['bytes'],tapRows=m['tapRows'],tapTruncated=m['tapTruncated'],manifestSHA256=hashlib.sha256((pathlib.Path(root)/'app-authority.json').read_bytes()).hexdigest())
def load_inputs(root):
 # Existing checker materializes inputs; explicitly bound its materialization too.
 tap=[];events=[];receipts=[];decoded_bytes=0
 for r in records(root):
  decoded_bytes+=len(json.dumps(r,separators=(',',':')).encode())
  if decoded_bytes>67108864:raise ValueError('CHECKER_MATERIALIZATION_BOUND')
  if r['source']!='CIM_PROCESS_NOTIFICATION':raise ValueError('UNEXPECTED_APPLICATION_SOURCE')
  if r['eventType'] in ('A-callback','A-enqueue'):tap.append(r['raw'])
  elif r['eventType']=='persistence':events.append(r['raw']['event']);receipts.append(r['raw']['receipt'])
  else:raise ValueError('UNEXPECTED_APPLICATION_RECORD')
 return tap,events,receipts
