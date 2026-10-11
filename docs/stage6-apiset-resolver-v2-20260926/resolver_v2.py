"""Offline provenance resolver; never runs imported tools or observer images.

Supported offline layout: API-set namespace v6, versioned api-/ext- names.
Matching uses the schema hash index, HashFactor and exact HashedLength/name
comparison. It does not rewrite versions or search for a nearby version.
"""
import ctypes, hashlib, json, platform, re, struct
from pathlib import Path

CLASSES=frozenset({'BUILD_INPUT_REQUIRED','BUILD_TOOL_RUNTIME_DEPENDENCY',
 'OUTPUT_RUNTIME_DEPENDENCY','CURRENT_HOST_MAPPING','CORROBORATIVE_ONLY',
 'NOT_REQUIRED_FOR_BUILD_COMPARABILITY'})
class ProvenanceError(Exception):pass
class SchemaUnsupported(ProvenanceError):pass
class Unresolved(ProvenanceError):pass
class Ambiguous(Unresolved):pass

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
 return h.hexdigest()

def identity(path):
 p=Path(path).resolve(strict=True)
 return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}

def verify_identity(record):
 if identity(record['path'])!=record:raise ProvenanceError('File identity drift: '+record['path'])

def normalize_contract(name):
 if not isinstance(name,str) or not name.isascii():raise Unresolved('Invalid API-set name')
 name=name.lower()
 if name.endswith('.dll'):name=name[:-4]
 if not re.fullmatch(r'(?:api|ext)-[a-z0-9-]+-l\d+-\d+-\d+',name):
  raise Unresolved('Unsupported API-set name syntax: '+name)
 return name

def hash_name(text,factor):
 result=0
 for ch in text.lower():result=(result*factor+ord(ch))&0xffffffff
 return result

class Buffer:
 def __init__(self,data):self.data=data
 def span(self,offset,length):
  if offset<0 or length<0 or offset>len(self.data) or length>len(self.data)-offset:
   raise ProvenanceError('Out-of-bounds data')
  return self.data[offset:offset+length]
 def u32(self,offset):return struct.unpack('<I',self.span(offset,4))[0]
 def u16(self,offset):return struct.unpack('<H',self.span(offset,2))[0]
 def text(self,offset,length):
  if offset%2 or length%2:raise ProvenanceError('Unaligned UTF-16 field')
  try:s=self.span(offset,length).decode('utf-16le')
  except UnicodeError as e:raise ProvenanceError('Malformed UTF-16') from e
  if '\0' in s:raise ProvenanceError('Embedded NUL')
  return s

class PE:
 def __init__(self,path):
  self.path=Path(path);self.b=Buffer(self.path.read_bytes());b=self.b
  if b.span(0,2)!=b'MZ':raise ProvenanceError('Invalid DOS header')
  p=b.u32(60)
  if b.span(p,4)!=b'PE\0\0':raise ProvenanceError('Invalid PE signature')
  self.machine=b.u16(p+4);self.op=p+24;magic=b.u16(self.op)
  if magic not in (0x20b,0x10b):raise ProvenanceError('Unsupported PE format')
  self.width=8 if magic==0x20b else 4;self.dd=self.op+(112 if self.width==8 else 96)
  self.directory_count=b.u32(self.dd-4);opt_size=b.u16(p+20)
  b.span(self.op,opt_size);self.sections=[]
  for i in range(b.u16(p+6)):
   q=self.op+opt_size+40*i;name=b.span(q,8).split(b'\0')[0].decode('ascii')
   self.sections.append({'name':name,'va':b.u32(q+12),'raw':b.u32(q+20),'rawsize':b.u32(q+16)})
 def offset(self,rva,size=1):
  for s in self.sections:
   n=rva-s['va']
   if 0<=n and n+size<=s['rawsize']:
    self.b.span(s['raw']+n,size);return s['raw']+n
  raise ProvenanceError('Unbacked PE RVA')
 def string(self,rva):
  o=self.offset(rva);tail=self.b.data[o:o+4096]
  if b'\0' not in tail:raise ProvenanceError('Unterminated PE string')
  try:return tail.split(b'\0')[0].decode('ascii')
  except UnicodeError as e:raise ProvenanceError('Invalid PE name') from e
 def section(self,name):
  matches=[s for s in self.sections if s['name']==name]
  if len(matches)!=1:raise ProvenanceError('Missing/ambiguous PE section')
  s=matches[0];return self.b.span(s['raw'],s['rawsize'])
 def imports(self):
  result=[];b=self.b
  for number,kind,width in [(1,'NORMAL',20),(13,'DELAY',32)]:
   if number>=self.directory_count:continue
   rva=b.u32(self.dd+8*number);length=b.u32(self.dd+8*number+4)
   if not rva:continue
   base=self.offset(rva,length);terminated=False
   for n in range(length//width):
    p=base+n*width
    if not any(b.span(p,width)):terminated=True;break
    if kind=='NORMAL':name_rva=b.u32(p+12);table=b.u32(p) or b.u32(p+16)
    else:
     if b.u32(p)!=1:raise ProvenanceError('Unsupported delay import attributes')
     name_rva=b.u32(p+4);table=b.u32(p+16)
    symbols=[]
    for index in range(100000):
     at=self.offset(table+index*self.width,self.width)
     value=int.from_bytes(b.span(at,self.width),'little')
     if value==0:break
     if value>>(self.width*8-1):symbols.append({'ordinal':value&65535})
     else:symbols.append({'name':self.string(value+2)})
    else:raise ProvenanceError('Unterminated import thunk')
    result.append({'exact_name':self.string(name_rva),'import_kind':kind,'symbols':symbols})
   if not terminated:raise ProvenanceError('Unterminated import descriptor')
  return result

class SchemaV6:
 def __init__(self,data,source=None):
  b=Buffer(data)
  if b.u32(0)!=6:raise SchemaUnsupported('Only namespace version 6 is supported')
  size=b.u32(4)
  if size<28 or size>len(data):raise ProvenanceError('Invalid namespace size')
  b=Buffer(data[:size]);self.source=source;self.version=6;self.size=size;self.flags=b.u32(8)
  count=b.u32(12);entries=b.u32(16);hashes=b.u32(20);self.factor=b.u32(24)
  if count>100000 or not self.factor:raise ProvenanceError('Invalid namespace count/hash factor')
  b.span(entries,count*24);b.span(hashes,count*8);self.entries=[]
  for index in range(count):
   p=entries+index*24;name=b.text(b.u32(p+4),b.u32(p+8));hashed=b.u32(p+12)
   if not name or not name.isascii() or hashed%2 or not 0<hashed<=len(name)*2:
    raise ProvenanceError('Malformed namespace entry')
   vcount=b.u32(p+20);voffset=b.u32(p+16)
   if vcount>100000:raise ProvenanceError('Invalid value count')
   b.span(voffset,vcount*20);values=[]
   for j in range(vcount):
    q=voffset+j*20
    values.append({'index':j,'flags':b.u32(q),'alias':b.text(b.u32(q+4),b.u32(q+8)),
                   'host':b.text(b.u32(q+12),b.u32(q+16)),
                   'name_offset':b.u32(q+4),'name_length':b.u32(q+8),
                   'value_offset':b.u32(q+12),'value_length':b.u32(q+16)})
   self.entries.append({'index':index,'flags':b.u32(p),'name':name,'name_offset':b.u32(p+4),
      'name_length':b.u32(p+8),'hashed_length':hashed,'hashed_name':name[:hashed//2],
      'value_offset':voffset,'value_count':vcount,'values':values})
  self.hash_entries=[];indices=[];last=-1
  for i in range(count):
   h=b.u32(hashes+8*i);index=b.u32(hashes+8*i+4)
   if index>=count or h<last:raise ProvenanceError('Invalid hash index')
   if hash_name(self.entries[index]['hashed_name'],self.factor)!=h:raise ProvenanceError('Schema hash mismatch')
   indices.append(index);self.hash_entries.append({'hash':h,'index':index});last=h
  if sorted(indices)!=list(range(count)):raise ProvenanceError('Duplicate/missing hash index')
 @classmethod
 def from_file(cls,path):return cls(PE(path).section('.apiset'),identity(path))
 def select(self,contract,importer):
  name=normalize_contract(contract);prefix=name[:name.rfind('-')];hashval=hash_name(prefix,self.factor)
  # Indexed hash plus exact full hashed-name equality; no startswith/nearest-version search.
  candidates=[self.entries[x['index']] for x in self.hash_entries if x['hash']==hashval
              and self.entries[x['index']]['hashed_length']==len(prefix)*2
              and self.entries[x['index']]['hashed_name'].lower()==prefix]
  if not candidates:raise Unresolved('Contract absent from supported schema index: '+contract)
  if len(candidates)!=1:raise Ambiguous('Multiple matching namespace entries: '+contract)
  entry=candidates[0];base=Path(importer).name.lower()
  overrides=[v for v in entry['values'] if v['alias'] and v['alias'].lower()==base]
  defaults=[v for v in entry['values'] if not v['alias']]
  if len(defaults)>1 or len(overrides)>1:raise Ambiguous('Ambiguous value mapping')
  selected=overrides or defaults
  if not selected or not selected[0]['host']:raise Unresolved('No nonempty applicable host')
  v=selected[0];validate_module(v['host'])
  return {'normalized_name':name,'query_hash':hashval,'selected_entry':entry,
          'selected_value':v,'importer':base,'importer_override':bool(overrides)}

def validate_module(name):
 if not re.fullmatch(r'[A-Za-z0-9_.-]+\.(?:dll|exe|sys|drv)',name,re.I) or '..' in name:
  raise ProvenanceError('Invalid physical module basename')

def documented_query(contract):
 try:
  dll=ctypes.WinDLL('api-ms-win-core-apiquery-l2-1-0.dll');fn=dll.GetApiSetModuleBaseName
 except (OSError,AttributeError):return {'status':'UNAVAILABLE'}
 fn.argtypes=[ctypes.c_char_p,ctypes.c_uint32,ctypes.c_wchar_p,ctypes.POINTER(ctypes.c_uint32)];fn.restype=ctypes.c_long
 buf=ctypes.create_unicode_buffer(260);length=ctypes.c_uint32()
 hr=fn(contract.encode('ascii'),260,buf,ctypes.byref(length))&0xffffffff
 if hr==0:return {'status':'SUCCESS','host':buf.value,'hresult':hr}
 return {'status':'E_NOTIMPL' if hr==0x80004001 else 'ERROR','hresult':hr}

def resolve_contract(schema,contract,importer,query=documented_query):
 normalized=normalize_contract(contract);q=query(contract)
 if q['status'] not in {'SUCCESS','UNAVAILABLE','E_NOTIMPL'}:raise Unresolved('Documented query failed: '+str(q))
 match=schema.select(contract,importer);value=match['selected_value'];method='OFFLINE_SCHEMA_V6_HASH_INDEX'
 if q['status']=='SUCCESS':
  validate_module(q['host'])
  if match['importer_override']:
   defaults=[v for v in match['selected_entry']['values'] if not v['alias']]
   if len(defaults)!=1 or defaults[0]['host'].lower()!=q['host'].lower():raise Unresolved('Documented/default schema contradiction')
   method='DOCUMENTED_DEFAULT_WITH_SCHEMA_IMPORTER_OVERRIDE'
  else:
   if value['host'].lower()!=q['host'].lower():raise Unresolved('Documented/schema contradiction')
   method='DOCUMENTED_QUERY_SCHEMA_AGREEMENT'
 return {'exact_contract':contract,'normalized_name':normalized,'status':'RESOLVED','method':method,
         'documented_query':q,'host':value['host'],'selection':match}

def resolve_physical(name,importer,toolroot,systemroot):
 validate_module(name)
 for root in [Path(importer).parent,Path(toolroot),Path(systemroot)]:
  p=root/name
  if p.is_file():return identity(p)
 raise Unresolved('Missing physical dependency: '+name+' imported by '+str(importer))

def import_evidence(importer,row,classification):
 if classification not in {'BUILD_TOOL_RUNTIME_DEPENDENCY','OUTPUT_RUNTIME_DEPENDENCY'}:
  raise ProvenanceError('Invalid import provenance class')
 return {'classification':classification,'importer':identity(importer),**row,
         'kind':'API_SET_CONTRACT' if row['exact_name'].lower().startswith(('api-','ext-')) else 'PHYSICAL_DLL'}

def partition(records):
 groups={k:[] for k in sorted(CLASSES)}
 for row in records:
  if row['classification'] not in groups:raise ProvenanceError('Unknown provenance class')
  groups[row['classification']].append(row)
 return groups

def host_binding(schema_path):
 import winreg
 with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r'SOFTWARE\Microsoft\Windows NT\CurrentVersion') as key:
  osid={n:winreg.QueryValueEx(key,n)[0] for n in ['CurrentBuildNumber','UBR','DisplayVersion','EditionID']}
 return {'os':osid,'architecture':platform.machine(),'schema_path':str(Path(schema_path)),
         'schema_sha256':sha(schema_path)}

def check_binding(actual,expected):
 if actual!=expected:raise ProvenanceError('OS/schema identity drift')
