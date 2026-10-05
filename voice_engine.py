"""Short-lived voice playback cache. No audio or reply text is written to disk."""
from collections import OrderedDict
import hashlib
import os
import re
import threading
import time
import providers


def prepare(text, limit=3900):
    text = providers.speech_text(text)
    if len(text) <= limit:
        return text
    prefix = text[:limit]
    endings = list(re.finditer(r'[.!?](?:\s|$)', prefix))
    if endings and endings[-1].end() > limit // 2:
        prefix = prefix[:endings[-1].end()].strip()
    else:
        prefix = prefix.rsplit(' ', 1)[0].rstrip(',;:') + '.'
    return prefix + ' The rest is available in the chat.'


class VoiceEngine:
    def __init__(self, max_bytes=8*1024*1024, ttl=120):
        self.cache = OrderedDict()
        self.lock = threading.Lock()
        self.max_bytes, self.ttl = max_bytes, ttl

    def synthesize(self, text, profile='auto'):
        text = prepare(text)
        if not text:
            raise ValueError('No spoken text remains.')
        # Include provider settings and credentials in a digest, never in output.
        settings = '\0'.join(os.getenv(k, '') for k in ('FISH_API_KEY','FISH_VOICE_ID','FISH_MODEL','OPENAI_API_KEY','DASHSCOPE_API_KEY','QWEN_TTS_VOICE','QWEN_TTS_MODEL','DASHSCOPE_BASE_URL','DASHSCOPE_TTS_URL'))
        key = hashlib.sha256((profile+'\0'+settings+'\0'+text).encode()).digest()
        with self.lock:
            now = time.monotonic()
            self.cache = OrderedDict((k,v) for k,v in self.cache.items() if now-v[0] < self.ttl)
            if key in self.cache:
                self.cache.move_to_end(key)
                return self.cache[key][1]
            audio = providers.speech(text, profile)
            if not isinstance(audio, bytes) or len(audio) < 100:
                raise providers.ProviderError('Voice provider returned no usable audio. Please retry.')
            if len(audio) <= self.max_bytes:
                self.cache[key] = (time.monotonic(), audio)
                while sum(len(v[1]) for v in self.cache.values()) > self.max_bytes:
                    self.cache.popitem(last=False)
            return audio
