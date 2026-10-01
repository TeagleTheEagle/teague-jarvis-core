import ctypes as c,ctypes.wintypes as w,json,pathlib
R=pathlib.Path(__file__).parent/'sharing-probe';R.mkdir(exist_ok=False)
k=c.WinDLL('kernel32',use_last_error=True)
k.MoveFileExW.argtypes=[w.LPCWSTR,w.LPCWSTR,w.DWORD];k.MoveFileExW.restype=w.BOOL
k.CreateFileW.argtypes=[w.LPCWSTR,w.DWORD,w.DWORD,c.c_void_p,w.DWORD,w.DWORD,w.HANDLE];k.CreateFileW.restype=w.HANDLE
k.CloseHandle.argtypes=[w.HANDLE]
rows=[]
for mode in ('no_reader','python_open_reader','explicit_share_delete'):
 for i in range(30):
  target=R/(mode+str(i)+'.json');tmp=R/(mode+str(i)+'.tmp')
  target.write_text('{"sequence":1}');tmp.write_text('{"sequence":2}')
  f=None;h=None
  if mode=='python_open_reader':f=target.open('r')
  elif mode=='explicit_share_delete':
   h=k.CreateFileW(str(target),0x80000000,1|2|4,None,3,0,None)
   if h==c.c_void_p(-1).value:raise c.WinError(c.get_last_error())
  c.set_last_error(0);ok=bool(k.MoveFileExW(str(tmp),str(target),1));error=0 if ok else c.get_last_error()
  if f:f.close()
  if h:k.CloseHandle(h)
  closed_result=None
  if not ok:
   closed_result=bool(k.MoveFileExW(str(tmp),str(target),1))
  rows.append({'Mode':mode,'Trial':i,'ReplacementSucceeded':ok,'WinError':error,'AfterReaderClosedSucceeded':closed_result})
(R.parent/'sharing-results.json').write_text(json.dumps(rows,indent=2))
for mode in ('no_reader','python_open_reader','explicit_share_delete'):
 a=[r for r in rows if r['Mode']==mode];print(mode,'success',sum(r['ReplacementSucceeded'] for r in a),'errors',[r['WinError'] for r in a if r['WinError']][:3])
