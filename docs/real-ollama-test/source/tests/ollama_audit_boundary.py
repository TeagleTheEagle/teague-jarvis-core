"""Exercise the actual TEST audit hook without making network requests."""
import sys,json,uuid,socket
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import stage4_runtime as r
root=r.exclusion.BASE/('TEST-STAGE4-'+uuid.uuid4().hex);root.mkdir();(root/'TEST_ONLY').write_text('NO PRODUCTION SERVICES')
data_id='TEST-'+uuid.uuid4().hex;r.provision(root,data_id)
checks=[]
with r.exclusion.Lock(root,'core.lock') as lock:
 c=r.Context(root,data_id,lock,{});r.construct_app(c)
 sock=SimpleNamespace(family=socket.AF_INET,type=socket.SOCK_STREAM)
 def denied(event,*args):
  try:sys.audit(event,*args)
  except r.Denied:checks.append({'event':event,'denied':True});return
  raise AssertionError(event+' unexpectedly allowed')
 denied('socket.connect',sock,('127.0.0.1',11434))
 c.allow_local_ollama=True
 sys.audit('socket.connect',sock,('127.0.0.1',11434));checks.append({'fixed_endpoint_allowed':True})
 for address in [('localhost',11434),('127.0.0.1',1),('192.168.1.1',11434),('api.openai.com',443),('::1',11434)]:denied('socket.connect',sock,address)
 denied('socket.getaddrinfo','localhost',11434,0,0,0)
 denied('socket.sendto',sock,('127.0.0.1',11434))
 print(json.dumps({'passed':len(checks),'checks':checks,'real_socket_operations':0}))
