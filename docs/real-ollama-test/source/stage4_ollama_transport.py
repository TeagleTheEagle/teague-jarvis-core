"""Bounded numeric-loopback TEST transport; no credentials, tools or model pull."""
import http.client
import json
import socket
import threading
import time
from stage4_provider_fallback import Failure

ADDRESS=('127.0.0.1',11434)
MODEL='qwen3:4b'


def permitted(address, family=socket.AF_INET, kind=socket.SOCK_STREAM):
    return (type(address) is tuple and len(address)==2 and
            type(address[0]) is str and type(address[1]) is int and
            address==ADDRESS and family==socket.AF_INET and kind==socket.SOCK_STREAM)


class LocalConnection(http.client.HTTPConnection):
    def connect(self):
        if not permitted((self.host,self.port)) or self._tunnel_host:
            raise Failure('DESTINATION_DENIED')
        self.sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.transport_socket=self.sock
        self.sock.settimeout(self.timeout)
        self.sock.connect(ADDRESS)  # No DNS, proxy, redirect or alternate port.


class Transport:
    def __init__(self, *, mode):
        if mode!='STAGE4_TEST':raise Failure('TEST_ONLY')
        self.measurements=[]

    def request(self,path,payload,cancel,deadline):
        if path not in ('/api/tags','/api/chat'):raise Failure('ENDPOINT_DENIED')
        if cancel.is_set():raise Failure('CANCELLED')
        remaining=deadline-time.monotonic()
        if remaining<=0:raise Failure('OLLAMA_TIMEOUT')
        conn=LocalConnection(*ADDRESS,timeout=min(remaining,20))
        finished=threading.Event()
        def interrupt():
            while not finished.wait(.025):
                if cancel.is_set() or time.monotonic()>=deadline:
                    # HTTPConnection drops sock after Connection: close headers;
                    # HTTPResponse still owns the live socket while reading.
                    sock=getattr(conn,'transport_socket',None)
                    if sock is not None:
                        try:sock.shutdown(socket.SHUT_RDWR)
                        except OSError:pass
                    return
        watcher=threading.Thread(target=interrupt,name='TEST-ollama-cancel',daemon=True)
        watcher.start()
        try:
            body=json.dumps(payload).encode() if payload is not None else None
            if body is not None and len(body)>65536:raise Failure('INPUT_TOO_LARGE')
            conn.request('POST' if payload is not None else 'GET',path,body,
                         {'Content-Type':'application/json','Connection':'close'})
            response=conn.getresponse()
            if response.status!=200:raise Failure('OLLAMA_HTTP_ERROR')
            raw=response.read(131073)
            if len(raw)>131072:raise Failure('OLLAMA_RESPONSE_TOO_LARGE')
            if cancel.is_set():raise Failure('CANCELLED')
            if time.monotonic()>=deadline:raise Failure('OLLAMA_TIMEOUT')
            def pairs(items):
                result={}
                for key,value in items:
                    if key in result:raise ValueError('duplicate')
                    result[key]=value
                return result
            value=json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
            if not isinstance(value,dict) or value.get('error'):raise Failure('OLLAMA_GENERATION_ERROR')
            return value
        except (TimeoutError,socket.timeout):
            raise Failure('CANCELLED' if cancel.is_set() else 'OLLAMA_TIMEOUT') from None
        except (OSError,http.client.HTTPException):
            raise Failure('CANCELLED' if cancel.is_set() else 'OLLAMA_TIMEOUT' if time.monotonic()>=deadline else 'OLLAMA_UNAVAILABLE') from None
        except (ValueError,UnicodeError):
            raise Failure('OLLAMA_MALFORMED_RESPONSE') from None
        finally:
            finished.set();conn.close()
            if 'response' in locals():response.close()
            watcher.join(.5)
            if watcher.is_alive():raise Failure('TRANSPORT_CLEANUP_UNCONFIRMED')

    def health(self,model,cancel,deadline):
        if model!=MODEL:raise Failure('MODEL_DENIED')
        value=self.request('/api/tags',None,cancel,min(deadline,time.monotonic()+2))
        return 'ONLINE' if any(m.get('name')==MODEL for m in value.get('models',[]) if isinstance(m,dict)) else 'MODEL_MISSING'

    def generate(self,messages,model,cancel,deadline):
        if model!=MODEL:raise Failure('MODEL_DENIED')
        if not isinstance(messages,list) or not messages or any(not isinstance(m,dict) or set(m)!={'role','content'} or m['role'] not in ('system','user','assistant') or not isinstance(m['content'],str) for m in messages):
            raise Failure('TEXT_ONLY_REQUIRED')
        if sum(len(m['content']) for m in messages)>12000:raise Failure('INPUT_TOO_LARGE')
        start=time.monotonic()
        value=self.request('/api/chat',{'model':MODEL,'messages':messages,'stream':False,'think':False,
            'keep_alive':30,'options':{'num_predict':256,'num_ctx':4096,'temperature':0}},cancel,deadline)
        message=value.get('message')
        if value.get('model')!=MODEL or value.get('done') is not True or value.get('done_reason')!='stop' or not isinstance(message,dict) or message.get('tool_calls') or message.get('thinking'):
            detail={'model_matches':value.get('model')==MODEL,'done':value.get('done') is True,
                    'done_reason':str(value.get('done_reason'))[:40],
                    'message_object':isinstance(message,dict),
                    'has_tools':bool(message.get('tool_calls')) if isinstance(message,dict) else None,
                    'has_thinking':bool(message.get('thinking')) if isinstance(message,dict) else None,
                    'content_length':len(message.get('content','')) if isinstance(message,dict) and isinstance(message.get('content',''),str) else None}
            raise Failure('OLLAMA_INVALID_OR_INCOMPLETE_RESPONSE '+json.dumps(detail,sort_keys=True))
        metrics={'wall_seconds':round(time.monotonic()-start,6),'time_to_first_token':None}
        for name in ('total_duration','load_duration','prompt_eval_count','prompt_eval_duration','eval_count','eval_duration'):
            n=value.get(name)
            if type(n) is int and n>=0:metrics[name]=n
        if metrics.get('eval_duration',0)>0:
            metrics['tokens_per_second']=metrics.get('eval_count',0)*1e9/metrics['eval_duration']
        self.measurements.append(metrics)
        return {'model':value['model'],'content':message.get('content'),'complete':True,'metrics':metrics}


def real_router():
    from stage4_provider_fallback import Router,HTTPFailure
    transport=Transport(mode='STAGE4_TEST')
    def primary(*args):raise HTTPFailure(429,'rate_limit_exceeded','7')
    router=Router(mode='STAGE4_TEST',primary=primary,health=transport.health,local=transport.generate,
                  configured_model='SIMULATED_OPENAI_NO_REQUEST',enabled=True,local_simulated=False)
    return router
