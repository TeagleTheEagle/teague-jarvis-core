"""Optional Windows audio playback. No voice selection or synthesis here."""
import asyncio
import ctypes
from dataclasses import dataclass
from pathlib import Path
import sys
import tempfile
import uuid
from .contracts import WearableError


@dataclass(frozen=True)
class EncodedAudio:
    data: bytes
    mime: str
    def validate(self):
        if self.mime!='audio/mpeg' or not isinstance(self.data,bytes) or not 100<=len(self.data)<=16*1024*1024:
            raise WearableError('INVALID_OUTPUT_AUDIO')
        return self


async def play_mp3(audio, started=None):
    audio.validate()
    if sys.platform!='win32':raise WearableError('WINDOWS_PLAYBACK_REQUIRED')
    alias='jarvis'+uuid.uuid4().hex
    def command(text):
        buffer=ctypes.create_unicode_buffer(256)
        if ctypes.windll.winmm.mciSendStringW(text,buffer,256,0):raise WearableError('AUDIO_PLAYBACK_FAILED')
        return buffer.value
    with tempfile.TemporaryDirectory(prefix='jarvis-voice-') as folder:
        path=Path(folder)/'reply.mp3';path.write_bytes(audio.data)
        opened=False
        try:
            command(f'open "{path}" type mpegvideo alias {alias}');opened=True
            command(f'play {alias}')
            if started:started()
            while command(f'status {alias} mode')=='playing':await asyncio.sleep(.05)
        finally:
            if opened:
                try:command(f'close {alias}')
                except WearableError:pass
