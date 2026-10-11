"""Best-effort comparison telemetry; never returns a prediction to Core execution."""
import json
import os
from pathlib import Path
import re
import threading
import time

from ollama_provider import OllamaError, OllamaProvider, validate


# Closed grammar avoids copying free-form notes, queries, secrets or history.
# These are eligibility filters, not a replacement for Core's command classifier.
ELIGIBLE = re.compile(
    r'(?:open (?:calculator|notepad|paint)|(?:what time is it|time|date|what is the date)'
    r'|(?:jarvis[, ]+)?(?:check your systems|check your health|run diagnostics|system health|health check)'
    r'|(?:what are|show|list)(?: my| the)?(?: active)? projects)[.!?]?', re.I)


class ShadowObserver:
    def __init__(self, root, provider=None):
        self.enabled = os.getenv('JARVIS_OLLAMA_SHADOW', '1') == '1'
        self.provider = provider or OllamaProvider()
        self.path = Path(root) / 'provider-shadow.jsonl'
        self.gate = threading.Lock()
        self.next_allowed = 0.0
        self.last = None
        self.worker = None
        self.skipped = 0

    def snapshot(self):
        return {'enabled': self.enabled, 'mode': 'SHADOW', 'authoritative': False,
                'health': dict(self.provider.health), 'last': self.last, 'skipped': self.skipped}

    def submit(self, request_id, text, command):
        try:
            if not self.enabled or not command or not ELIGIBLE.fullmatch(text) or len(text) > 120:
                return
            name, args = command
            if name not in ('open_app', 'time_now', 'system_health', 'project_catalog'):
                return
            authoritative = validate({'intent': name, 'target': args.get('app', 'unspecified'),
                                      'action': 'classify', 'parameters': {}})
            if not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}', request_id):
                return
            if not self.gate.acquire(blocking=False):
                self.skipped += 1
                return
            if time.monotonic() < self.next_allowed:
                self.skipped += 1
                self.gate.release()
                return
            try:
                self.worker = threading.Thread(target=self._evaluate,
                    args=(request_id, text, authoritative), daemon=True, name='ollama-shadow')
                self.worker.start()
            except Exception:
                self.gate.release()
        except Exception:
            # Even broken optional telemetry must not affect the authoritative request.
            return

    def _evaluate(self, request_id, text, authoritative):
        record = {'timestamp': time.time(), 'request_id': request_id, 'mode': 'SHADOW',
                  'authoritative': authoritative, 'qwen': None, 'match': None,
                  'schema_valid': False, 'error': None, 'model': self.provider.model,
                  'latency_ms': None, 'load_duration_ms': None, 'lifecycle': 'unknown'}
        started = time.perf_counter()
        classification_started = None
        failed = True
        try:
            health = self.provider.health_check()
            record['health'] = health
            if health['status'] != 'ONLINE':
                raise OllamaError(health.get('error') or 'unavailable')
            record['lifecycle'] = 'warm' if health['loaded_before_request'] else 'cold'
            classification_started = time.perf_counter()
            result = self.provider.classify_intent(text)
            prediction = validate(result['prediction'])
            record.update(qwen=prediction, match=prediction == authoritative, schema_valid=True,
                          latency_ms=result['latency_ms'], load_duration_ms=result['load_duration_ms'],
                          lifecycle='warm' if health['loaded_before_request'] else 'cold')
            failed = False
        except Exception as exc:
            safe_codes = {'offline', 'timeout', 'model_missing', 'http_error', 'malformed_json',
                          'invalid_json', 'invalid_schema', 'invalid_envelope', 'unknown_intent',
                          'invalid_target', 'duplicate_json_field', 'incomplete_response',
                          'unexpected_output', 'response_too_large', 'unavailable'}
            record['error'] = str(exc) if isinstance(exc, OllamaError) and str(exc) in safe_codes else 'shadow_error'
            self.provider.health = {**self.provider.health, 'status': 'OFFLINE' if record['error'] == 'offline' else 'DEGRADED'}
        finally:
            if record['latency_ms'] is None and classification_started is not None:
                record['latency_ms'] = round((time.perf_counter()-classification_started)*1000, 3)
            record['total_latency_ms'] = round((time.perf_counter()-started)*1000, 3)
            record['provider_health'] = self.provider.health['status']
            self.last = record
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                if self.path.exists() and self.path.stat().st_size > 1024*1024:
                    self.path.replace(self.path.with_suffix('.previous.jsonl'))
                with self.path.open('a', encoding='utf-8') as out:
                    out.write(json.dumps(record, allow_nan=False) + '\n')
            except Exception:
                self.last = {**record, 'logging_error': 'record_write_failed'}
            self.next_allowed = time.monotonic() + (60 if failed else 5)
            self.gate.release()


def observe(observer, request_id, text, command):
    """Explicit non-propagating seam. No return value is consumed by the caller."""
    try:
        observer.submit(request_id, text, command)
    except Exception:
        pass
