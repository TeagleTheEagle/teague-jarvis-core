"""Disposable regression guard; no production data, credentials or network."""
import io,os,pathlib,sys,tempfile,unittest,weakref
ROOT=pathlib.Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));os.chdir(ROOT)
for key in list(os.environ):
 if any(x in key.upper() for x in ('API_KEY','SECRET','TOKEN','PASSWORD')):os.environ.pop(key,None)
original_read=pathlib.Path.read_text
pathlib.Path.read_text=lambda self,*a,**k:'' if self.resolve()==ROOT/'.env' else original_read(self,*a,**k)
original_open=pathlib.Path.open
pathlib.Path.open=lambda self,*a,**k:io.StringIO('') if self.resolve()==ROOT/'.env' else original_open(self,*a,**k)
bound_sockets=weakref.WeakSet()
def audit(event,args):
 if event=='socket.bind':
  address=args[1]
  if not isinstance(address,tuple) or address[0] not in ('127.0.0.1','::1'):raise PermissionError('TEST non-loopback bind denied')
  bound_sockets.add(args[0])
 if event=='socket.connect':
  address=args[1];allowed=False
  if isinstance(address,tuple) and address[0] in ('127.0.0.1','::1'):
   for bound in list(bound_sockets):
    try:
     if bound.getsockname()[:2]==address[:2]:allowed=True;break
    except OSError:pass
  if not allowed:raise PermissionError('TEST connection not to an own-process fixture denied')
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  path=pathlib.Path(os.fsdecode(args[0])).resolve()
  if path==ROOT/'.env' or path.is_relative_to(ROOT/'data') or path==ROOT/'desktop/.jarvis-session.json':raise PermissionError('TEST production data read/write denied')
  mode=args[1];flags=args[2] if len(args)>2 and isinstance(args[2],int) else 0
  writing=(isinstance(mode,str) and any(c in mode for c in 'wa+')) or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)
  if writing and path.is_relative_to(ROOT) and not path.is_relative_to(ROOT/'tests') and not path.is_relative_to(ROOT/'docs/lifecycle-stage4-evidence'):
   raise PermissionError('TEST production source write denied')
sys.addaudithook(audit)
import development
original_history=development.history
with tempfile.TemporaryDirectory(prefix='STAGE4_TEST-regression-history-') as temp:
 fixture=pathlib.Path(temp);(fixture/'data/development').mkdir(parents=True)
 development.history=lambda root,*a,**k:original_history(fixture if pathlib.Path(root).resolve()==ROOT else root,*a,**k)
 result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover(str(ROOT),pattern='test_*.py',top_level_dir=str(ROOT)))
 raise SystemExit(not result.wasSuccessful())
