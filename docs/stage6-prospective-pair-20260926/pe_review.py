"""Read PE metadata without loading or executing the image."""
import struct
from pathlib import Path
def inspect(path):
 b=Path(path).read_bytes();u16=lambda o:struct.unpack_from('<H',b,o)[0];u32=lambda o:struct.unpack_from('<I',b,o)[0]
 if b[:2]!=b'MZ':raise ValueError('not PE')
 pe=u32(60);assert b[pe:pe+4]==b'PE\0\0'
 n=u16(pe+6);sz=u16(pe+20);op=pe+24;magic=u16(op);dd=op+(112 if magic==523 else 96);sec=op+sz
 sections=[]
 for i in range(n):
  o=sec+i*40;sections.append({'name':b[o:o+8].split(b'\0')[0].decode(),'vsize':u32(o+8),'va':u32(o+12),'rawsize':u32(o+16),'raw':u32(o+20)})
 def off(rva):
  for s in sections:
   if s['va']<=rva<s['va']+max(s['vsize'],s['rawsize']):return s['raw']+rva-s['va']
  if rva<u32(op+60):return rva
  raise ValueError('unmapped RVA')
 def cstr(rva):
  p=off(rva);return b[p:b.index(b'\0',p)].decode(errors='replace')
 imports=[];rva=u32(dd+8)
 if rva:
  p=off(rva)
  while any(b[p:p+20]):imports.append(cstr(u32(p+12)));p+=20
 delayed=[];rva=u32(dd+13*8)
 if rva:
  p=off(rva)
  while any(b[p:p+32]):
   if u32(p)&1:delayed.append(cstr(u32(p+4)))
   else:raise ValueError('VA delay import unsupported')
   p+=32
 debug=[];rva=u32(dd+6*8);count=u32(dd+6*8+4)//28
 if rva:
  p=off(rva)
  for i in range(count):
   q=p+28*i;kind=u32(q+12);size=u32(q+16);raw=u32(q+24);item={'type':kind,'size':size,'timestamp':u32(q+4)}
   if kind==2 and b[raw:raw+4]==b'RSDS':item.update({'guid':b[raw+4:raw+20].hex(),'age':u32(raw+20),'pdb':b[raw+24:raw+size].split(b'\0')[0].decode(errors='replace')})
   debug.append(item)
 return {'machine':hex(u16(pe+4)),'timestamp':u32(pe+8),'linkerVersion':f'{b[op+2]}.{b[op+3]}','characteristics':hex(u16(pe+22)),'dllCharacteristics':hex(u16(op+70)),'entryRVA':u32(op+16),'imports':imports,'delayImports':delayed,'debug':debug,'sections':sections}

def apiset(path):
 b=Path(path).read_bytes();info=inspect(path);s=next(x for x in info['sections'] if x['name']=='.apiset');b=b[s['raw']:s['raw']+s['rawsize']]
 u=lambda o:struct.unpack_from('<I',b,o)[0]
 assert u(0)==6,'Unsupported API set schema'
 def text(o,n):return b[o:o+n].decode('utf-16le')
 result={}
 for i in range(u(12)):
  p=u(16)+24*i;name=text(u(p+4),u(p+8));values=[]
  for j in range(u(p+20)):
   v=u(p+16)+20*j;values.append(text(u(v+12),u(v+16)))
  result[name.casefold()]=values
 return result
