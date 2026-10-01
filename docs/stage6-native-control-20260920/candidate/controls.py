"""Explicitly inherited anonymous marker mapping; no file-backed markers."""
import ctypes as c,ctypes.wintypes as w,subprocess,json,pathlib,os
from workspace import CODE
from probe_timing import Probe,K
CONFIG=json.loads((CODE/'controls-config.json').read_text());VARIANTS=CONFIG['variants']
class SA(c.Structure):_fields_=[('length',w.DWORD),('descriptor',c.c_void_p),('inherit',w.BOOL)]
K.CreateFileMappingW.argtypes=[w.HANDLE,c.POINTER(SA),w.DWORD,w.DWORD,w.DWORD,w.LPCWSTR];K.CreateFileMappingW.restype=w.HANDLE
K.MapViewOfFile.argtypes=[w.HANDLE,w.DWORD,w.DWORD,w.DWORD,c.c_size_t];K.MapViewOfFile.restype=c.c_void_p
K.UnmapViewOfFile.argtypes=[c.c_void_p];K.CloseHandle.argtypes=[w.HANDLE]
class NativeProbe(Probe):
 def __init__(self,exe,mode,variant):
  sa=SA(c.sizeof(SA),None,True);self.mapping=K.CreateFileMappingW(w.HANDLE(-1),c.byref(sa),4,0,4096,None)
  if not self.mapping:raise c.WinError(c.get_last_error())
  self.view=K.MapViewOfFile(self.mapping,6,0,0,4096)
  if not self.view:K.CloseHandle(self.mapping);raise c.WinError(c.get_last_error())
  si=subprocess.STARTUPINFO();si.lpAttributeList={'handle_list':[self.mapping]}
  try:super().__init__(exe,[str(mode),format(self.mapping,'x')],si)
  except BaseException:K.UnmapViewOfFile(self.view);K.CloseHandle(self.mapping);raise
  self.row['control']=variant;self.row['markerProtocol']='anonymous explicitly inherited mapping; timing/checksum only'
 def finish_observation(self):
  super().finish_observation()
  values=list((c.c_longlong*8).from_address(self.view))
  self.row['nativeMarkers']=dict(zip(('magic','firstActivityQpc','workBeginQpc','workEndQpc','exitBeginQpc','result','mode','pid'),values))
  K.UnmapViewOfFile(self.view);K.CloseHandle(self.mapping)
  if values[0]!=0x4a365052 or values[7]!=self.process.pid or not (values[1]<=values[2]<=values[3]<=values[4]):raise RuntimeError('Native marker identity/order invalid')
def make_probe(variant):
 if variant not in VARIANTS:raise ValueError('Unapproved control')
 kind,volume=variant.split('_')
 if kind=='C':
  p=Probe(CODE/'J6Probe.exe');p.row['control']=variant;p.row['nativeMarkers']=None;return p
 base=CODE if volume=='D' else pathlib.Path(CONFIG['c_image_dir'])
 return NativeProbe(base/('J6ProbeToken.exe' if kind=='D' else 'J6ProbeNative.exe'),{'A':0,'B':1,'D':2}[kind],variant)
