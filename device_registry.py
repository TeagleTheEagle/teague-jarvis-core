"""Core-owned device presence and capability planning. No device intelligence."""
import threading
import time


class DeviceRegistry:
    def __init__(self, clock=time.monotonic):
        self.clock=clock;self.lock=threading.RLock();self.devices={};self.requests={}

    def register(self, device_id, capabilities, *, ready=(), ttl=60, simulated=False):
        capabilities=frozenset(capabilities);ready=frozenset(ready)
        if not isinstance(device_id,str) or not device_id or not ready<=capabilities or not 0<ttl<=3600:raise ValueError('Invalid device registration.')
        with self.lock:
            self.devices[device_id]={'capabilities':capabilities,'ready':ready,'expires':self.clock()+ttl,'ttl':ttl,'simulated':bool(simulated)}

    def heartbeat(self, device_id):
        with self.lock:
            device=self.devices[device_id];device['expires']=self.clock()+device['ttl']

    def disconnect(self, device_id):
        with self.lock:
            if device_id in self.devices:self.devices[device_id]['expires']=0
            self.requests={k:v for k,v in self.requests.items() if v!=device_id}

    def forget(self, device_id):
        """A device that was revoked: gone from presence altogether, not merely disconnected."""
        with self.lock:
            self.devices.pop(device_id,None)
            self.requests={k:v for k,v in self.requests.items() if v!=device_id}

    def snapshot(self):
        with self.lock:
            return [{'device_id':ident,'connected':d['expires']>self.clock(),'capabilities':sorted(d['capabilities']),
                     'ready':sorted(d['ready']) if d['expires']>self.clock() else [],'simulated':d['simulated']}
                    for ident,d in self.devices.items()]

    def begin(self, request_id, device_id):
        with self.lock:
            if device_id not in self.devices or self.devices[device_id]['expires']<=self.clock():raise ValueError('Device offline.')
            self.requests[request_id]=device_id

    def finish(self, request_id):
        with self.lock:self.requests.pop(request_id,None)

    def interaction(self, request_id):
        with self.lock:return self.requests.get(request_id)

    def plan(self, request_id, requirements, preferred=None, allow_simulated=False):
        """Plan only. Registration is NOT permission to execute actions."""
        with self.lock:
            source=self.requests.get(request_id);preferred=preferred or {};steps=[]
            for role,capability in requirements.items():
                candidates=[d['device_id'] for d in self.snapshot() if d['connected'] and capability in d['ready'] and (allow_simulated or not d['simulated'])]
                wanted=preferred.get(role)
                selected=wanted if wanted in candidates else source if source in candidates else sorted(candidates)[0] if candidates else None
                steps.append({'role':role,'capability':capability,'device_id':selected,'status':'planned' if selected else 'unavailable'})
            selected={s['device_id'] for s in steps if s['device_id']}
            return {'request_id':request_id,'interaction_device':source,'steps':steps,'cooperation':len(selected)>1,
                    'executable':False,'requires_authorization':True}
