"""TEST ONLY pinned-key bootstrap; no production imports or activation path."""
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import time
from urllib.parse import urlsplit
import pipe_transport as pt

Denied=pt.Rejected
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()
def proof(key,label,value):return hmac.new(key,label.encode()+b'\0'+canonical(value),hashlib.sha256).hexdigest()
def digest(value):return hashlib.sha256(value.encode()).hexdigest()
def require(test,reason):
    if not test:raise Denied(reason)
def fields(value,names):require(type(value)==dict and set(value)==set(names),'UNKNOWN_FIELDS')
def negotiate(client,core):
    for pair in (client,core):
        require(type(pair)==list and len(pair)==2 and all(type(n)==int for n in pair) and 2<=pair[0]<=pair[1]<=3,'PROTOCOL_RANGE')
    result=min(client[1],core[1]);require(result>=max(client[0],core[0]),'PROTOCOL_INCOMPATIBLE');return result

def origin_allowed(url,expected):
    try:
        a,b=urlsplit(url),urlsplit(expected)
        return (a.scheme==b.scheme=='http' and a.hostname==b.hostname=='127.0.0.1'
                and a.port==b.port and a.port is not None and not a.username and not a.password
                and not b.username and not b.password and not any(x in url for x in ('\\','\r','\n','\t')))
    except ValueError:return False

def descriptor_valid(value,expected):
    return type(value)==dict and set(value)=={'endpoint','identity'} and value==expected

def validate_identity(value,expected):
    require(value==expected,'CORE_IDENTITY')
    require(value.get('mode')=='TEST' and expected.get('mode')=='TEST','MODE_MISMATCH')
    require(pt.identity(value['pid'])=={k:value[k] for k in ('pid','created','exe_digest')},'CORE_PROCESS_IDENTITY')

SCOPES={'attach','status','test','media','lifecycle'}
class Authority:
    def __init__(self,identity,enrollments,root,ttl=1):
        self.identity=identity;self.enrollments=enrollments;self.root=Path(root);self.ttl=ttl;self.sessions={}
    def active(self):
        require(not (self.root/'stop').exists(),'STOPPED')
        validate_identity(self.identity,self.identity)
    def operation(self,client,request,selected):
        fields(request,('op','token','args'));op=request['op'];args=request['args']
        require(type(op)==str and type(args)==dict,'BAD_REQUEST')
        allowed={'attach','status','renew','revoke','media','start','stop','restart','maintenance','revoke_client'}
        require(op in allowed,'UNKNOWN_OPERATION')
        self.active();enrolled=self.enrollments[client];require(enrolled['enabled'],'ENROLLMENT_REVOKED')
        if op=='attach':
            fields(args,('scopes',));requested=args['scopes']
            require(type(requested)==list and all(type(s)==str for s in requested),'SCOPE')
            require(set(requested)<=set(enrolled['scopes']) and {'attach','test'}<=set(requested),'SCOPE')
            require(request['token'] is None,'UNEXPECTED_TOKEN')
            require(len(self.sessions)<128,'SESSION_LIMIT')
            return self.issue(client,set(requested),selected)
        token=request['token'];require(type(token)==str and len(token)==64,'TOKEN_MALFORMED')
        record=self.sessions.get(digest(token));require(record is not None,'TOKEN_UNKNOWN')
        require(record['client']==client,'WRONG_CLIENT')
        require(record['identity']==self.identity,'TOKEN_INSTANCE')
        require(time.monotonic()<record['expires'],'TOKEN_EXPIRED')
        require(record['protocol']==selected,'TOKEN_PROTOCOL')
        needed='lifecycle' if op in ('start','stop','restart','maintenance','revoke_client') else 'media' if op=='media' else 'status' if op=='status' else 'attach'
        require(needed in record['scopes'],'SCOPE')
        if op=='revoke_client':
            fields(args,('client',));require(args['client'] in self.enrollments,'UNKNOWN_CLIENT')
            self.enrollments[args['client']]['enabled']=False
            self.sessions={key:value for key,value in self.sessions.items() if value['client']!=args['client']}
            return {'result':'CLIENT_REVOKED'}
        fields(args,())
        if op in ('renew','revoke'):
            del self.sessions[digest(token)]
            if op=='renew':return self.issue(client,record['scopes'],selected)
            return {'result':'REVOKED'}
        return {'result':'ALLOWED','scope':needed,'identity':self.identity,'tool_authorized':False,'lifecycle_executed':False}
    def issue(self,client,scopes,protocol):
        token=secrets.token_hex(32)
        self.sessions[digest(token)]={'client':client,'identity':dict(self.identity),'scopes':scopes,'protocol':protocol,'expires':time.monotonic()+self.ttl}
        return {'result':'ATTACHED','token':token,'identity':self.identity,'protocol':protocol,'scopes':sorted(scopes),'tool_authorized':False}

def serve_one(pipe,authority,server_key,behavior):
    peer=pipe.peer(server=True)
    hello=pipe.receive();fields(hello,('client','nonce','range'))
    require(type(hello['nonce'])==str and len(hello['nonce'])==64,'NONCE')
    require(type(hello['client'])==str,'CLIENT')
    entry=authority.enrollments.get(hello['client']);require(entry is not None and entry['enabled'],'NOT_ENROLLED')
    require(peer['exe_digest']==entry['exe_digest'],'CLIENT_EXECUTABLE')
    selected=negotiate(hello['range'],authority.identity['protocol'])
    require(hello['range']==entry['protocol'],'CLIENT_PROTOCOL')
    authority.active()
    transcript={'hello':hello,'server_nonce':secrets.token_hex(32),'identity':authority.identity,'selected':selected,'peer':peer}
    if behavior=='crash-handshake':os._exit(81)
    signed=proof(server_key,'server',transcript)
    if behavior=='fake-proof':signed='0'*64
    if behavior=='fake-health':
        pipe.send({'healthy':True,'application_id':'teague-industries'});return
    if behavior=='downgrade':transcript['selected']=2
    if behavior=='replay':transcript['hello']['nonce']='0'*64
    pipe.send({'transcript':transcript,'proof':signed})
    answer=pipe.receive();fields(answer,('proof',))
    require(type(answer['proof'])==str and hmac.compare_digest(answer['proof'],proof(entry['key'],'client',transcript)),'CLIENT_PROOF')
    response=authority.operation(hello['client'],pipe.receive(),selected)
    pipe.send(response)

def server(name,identity,enrollments,root,key,control,stop,ttl=1,behavior='normal'):
    # multiprocessing passes TEST secrets in memory; remove unrelated inherited environment.
    for name_ in list(os.environ):
        if name_.upper() not in ('SYSTEMROOT','WINDIR','TEMP','TMP'):os.environ.pop(name_,None)
    auth=Authority(identity,enrollments,root,ttl);first=True
    while not stop.is_set():
        pipe=None
        try:
            pipe=pt.listen(name)
            if first:
                control.send({'peer':pt.identity(os.getpid()),'acl':pt.acl(pipe),'remote_reject':True});first=False
            pipe.io('connect');pipe.deadline=time.monotonic()+5
            try:serve_one(pipe,auth,key,behavior)
            except (Denied,OSError,ValueError,TypeError,KeyError):
                try:pipe.send({'result':'DENIED'})
                except (Denied,OSError):pass
        except (Denied,OSError):
            if first:
                control.send({'failed':True});return
        finally:
            if pipe:pipe.close()

def client(name,pinned_peer,expected,key,client_id,client_key,request,protocol=None,drop=False):
    pipe=pt.connect(name)
    try:
        require(pipe.peer()==pinned_peer,'BOOTSTRAP_PROCESS_IDENTITY')
        hello={'client':client_id,'nonce':secrets.token_hex(32),'range':protocol or [2,3]}
        pipe.send(hello);response=pipe.receive();fields(response,('transcript','proof'))
        t=response['transcript'];fields(t,('hello','server_nonce','identity','selected','peer'))
        require(t['hello']==hello,'REPLAY')
        require(type(response['proof'])==str and hmac.compare_digest(response['proof'],proof(key,'server',t)),'SERVER_PROOF')
        validate_identity(t['identity'],expected)
        require(t['peer']==pt.identity(os.getpid()),'CLIENT_PROCESS_BINDING')
        require(t['selected']==negotiate(hello['range'],expected['protocol']),'DOWNGRADE')
        if drop=='crash':os._exit(82)
        if drop:return {'result':'DROPPED_BEFORE_CLIENT_PROOF'}
        pipe.send({'proof':proof(client_key,'client',t)})
        pipe.send(request)
        return pipe.receive()
    finally:pipe.close()
