"""Read-only Windows path spelling evidence; never opens a VM/data file."""
import ctypes,pathlib,json,sys,time
def capture(root):
 k=ctypes.WinDLL('kernel32',use_last_error=True);k.QueryDosDeviceW.argtypes=[ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_ulong];k.QueryDosDeviceW.restype=ctypes.c_ulong
 mapping={}
 for drive in ('C:','D:'):
  b=ctypes.create_unicode_buffer(32768)
  if not k.QueryDosDeviceW(drive,b,len(b)):raise ctypes.WinError(ctypes.get_last_error())
  mapping[drive]=b.value
 p=pathlib.Path(root)/'volume-map.json'
 with p.open('x') as f:json.dump(dict(mapping=mapping,capturedMonotonicNs=time.perf_counter_ns(),mechanism='QueryDosDeviceW; read-only'),f,indent=2)
 return mapping
if __name__=='__main__':capture(sys.argv[1])
