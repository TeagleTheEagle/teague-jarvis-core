"""Offline STAGE4_TEST routing only. No sockets, credentials, App or Store.

Transports are supplied by trusted TEST setup, never a renderer or environment.
They receive a cancellation event and an absolute monotonic deadline. They must
return buffered envelopes; this module never executes or returns tools.
"""
import copy
import datetime
import email.utils
import math
import threading
import time


class Failure(Exception):
    pass


class HTTPFailure(Exception):
    def __init__(self, status, code=None, retry_after=None):
        self.status, self.code, self.retry_after = status, code, retry_after


def classify(error, now=None):
    reason = 'openai_unavailable'
    retry = None
    if error.status == 429:
        reason = {'rate_limit_exceeded':'temporary_rate_limit',
                  'insufficient_quota':'quota_exhausted'}.get(error.code, 'other_429')
        if reason == 'temporary_rate_limit':
            try:
                retry = float(error.retry_after)
            except (TypeError, ValueError):
                try:
                    stamp = email.utils.parsedate_to_datetime(error.retry_after)
                    retry = stamp.timestamp() - (time.time() if now is None else now)
                except (TypeError, ValueError, OverflowError):
                    retry = None
            if retry is not None:
                retry = max(0, math.ceil(retry)) if math.isfinite(retry) else None
    elif error.status not in (500, 502, 503, 504):
        reason = 'primary_error_not_eligible'
    return {'reason':reason, 'http_status':error.status, 'retry_after_seconds':retry}


class Router:
    def __init__(self, *, mode, primary, health, local, configured_model,
                 enabled=False, clock=time.monotonic, local_simulated=True):
        if mode != 'STAGE4_TEST':
            raise Failure('TEST_ONLY')
        self.primary, self.health, self.local = primary, health, local
        self.configured_model, self.enabled = configured_model, enabled
        self.local_simulated = local_simulated
        self.local_model = 'qwen3:4b'
        self.clock = clock
        self.records = {}
        self.lock = threading.RLock()

    def status(self, request_id):
        # Caller must enforce authenticated ownership before exposing this record.
        with self.lock:
            return copy.deepcopy(self.records.get(request_id))

    def generate(self, request_id, messages, cancel, *, tool_attempted,
                 partial_output, vision=False, requires_tools=False, deadline=None):
        with self.lock:
            if request_id in self.records:
                raise Failure('DUPLICATE_PROVIDER_EXECUTION_REFUSED')
            record = dict(request_id=request_id, mode='STAGE4_TEST', simulated=True,
                          configured_model=self.configured_model, attempts=[],
                          actual_final_provider=None, actual_final_model=None,
                          fallback=False, fallback_reason=None, status='RUNNING')
            self.records[request_id] = record
        deadline = min(deadline if deadline is not None else self.clock()+20, self.clock()+20)
        def check():
            if cancel.is_set(): raise Failure('CANCELLED')
            if self.clock() >= deadline: raise Failure('DEADLINE_EXCEEDED')
        def finish(provider, envelope):
            check()
            # Do not infer actual model from configuration. Missing provenance fails.
            if not isinstance(envelope, dict): raise Failure('INVALID_RESPONSE')
            model, text = envelope.get('model'), envelope.get('content')
            if not isinstance(model,str) or not model or len(model)>200:
                raise Failure('ACTUAL_MODEL_UNAVAILABLE')
            if not isinstance(text,str) or not text.strip() or len(text)>32000:
                raise Failure('INVALID_RESPONSE')
            if envelope.get('tool_calls') or envelope.get('complete') is not True:
                raise Failure('UNSUPPORTED_OR_INCOMPLETE_RESPONSE')
            if provider == 'Ollama' and model != self.local_model:
                raise Failure('UNEXPECTED_LOCAL_MODEL')
            with self.lock:
                record.update(actual_final_provider=provider,actual_final_model=model,status='GENERATED')
                record['simulated'] = provider != 'Ollama' or self.local_simulated
                if 'metrics' in envelope:record['generation_metrics']=envelope['metrics']
            return {'role':'assistant','content':text}
        try:
            check()
            record['attempts'].append({'provider':'OpenAI','requested_model':self.configured_model,'simulated':True,'network_request':False})
            try:
                envelope = self.primary(copy.deepcopy(messages), self.configured_model, cancel, deadline)
            except HTTPFailure as error:
                detail = classify(error)
                record['primary_failure'] = detail
                record['fallback_reason'] = detail['reason']
                if detail['reason'] == 'primary_error_not_eligible':
                    raise Failure('PRIMARY_ERROR_NOT_ELIGIBLE')
            else:
                return finish('OpenAI', envelope)
            check()
            if not self.enabled: raise Failure('FALLBACK_DISABLED')
            if tool_attempted or partial_output:
                raise Failure('FALLBACK_UNSAFE_PRIOR_WORK')
            if vision or requires_tools or any(m.get('role') not in ('system','user','assistant')
                    or not isinstance(m.get('content'),str) or m.get('tool_calls') for m in messages):
                raise Failure('FALLBACK_UNSUPPORTED_REQUEST')
            if sum(len(m['content']) for m in messages)>12000:
                raise Failure('FALLBACK_CONTEXT_UNSUPPORTED')
            state = self.health(self.local_model, cancel, deadline)
            check()
            if state != 'ONLINE':
                raise Failure('FALLBACK_'+(state if state in ('OFFLINE','DISABLED','UNHEALTHY','MODEL_MISSING') else 'UNAVAILABLE'))
            record['attempts'].append({'provider':'Ollama','requested_model':self.local_model,'simulated':self.local_simulated,'network_request':not self.local_simulated})
            record['fallback'] = True
            return finish('Ollama', self.local(copy.deepcopy(messages), self.local_model, cancel, deadline))
        except Exception as error:
            code = str(error) if isinstance(error,Failure) else 'PROVIDER_GENERATION_FAILED'
            with self.lock:
                record.update(status='FAILED', failure=code)
            reason = record.get('fallback_reason')
            raise Failure((reason+': ' if reason else '')+code) from None


def offline_router(scenario='openai'):
    """Fixed scenario selected by trusted TEST parent; never live inference."""
    if scenario not in ('openai','temporary','quota','offline','generation-failure'):
        raise Failure('UNKNOWN_TEST_SCENARIO')
    def primary(messages, model, cancel, deadline):
        if scenario != 'openai':
            raise HTTPFailure(429,'insufficient_quota' if scenario=='quota' else 'rate_limit_exceeded','7')
        return {'model':'openai-offline-fixture','content':'STAGE4_TEST simulated OpenAI text-only answer. No actions performed.','complete':True}
    def health(model,cancel,deadline):
        return 'OFFLINE' if scenario=='offline' else 'ONLINE'
    def local(messages,model,cancel,deadline):
        if scenario=='generation-failure': raise Failure('LOCAL_GENERATION_FAILED')
        return {'model':'qwen3:4b','content':'STAGE4_TEST simulated Qwen text-only answer. No actions performed.','complete':True}
    return Router(mode='STAGE4_TEST',primary=primary,health=health,local=local,
                  configured_model='openai-requested-fixture',enabled=True)
