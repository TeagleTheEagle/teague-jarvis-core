"""Bounded media and device contracts; independent of Meta and JARVIS providers."""
from dataclasses import dataclass
from typing import Protocol, AsyncIterator
import re


class WearableError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', value):
        raise WearableError('INVALID_ID')
    return value


@dataclass(frozen=True)
class Audio:
    pcm: bytes
    sample_rate: int = 16000
    channels: int = 1

    def validate(self):
        if (type(self.pcm) is not bytes or self.sample_rate != 16000 or self.channels != 1
                or not 3200 <= len(self.pcm) <= 960000 or len(self.pcm) % 2):
            raise WearableError('INVALID_AUDIO')
        return self


@dataclass(frozen=True)
class Image:
    data: bytes
    mime: str

    def validate(self):
        if type(self.data) is not bytes or not 8 <= len(self.data) <= 2*1024*1024:
            raise WearableError('INVALID_IMAGE')
        signatures = {'image/png': b'\x89PNG\r\n\x1a\n', 'image/jpeg': b'\xff\xd8\xff'}
        if self.mime not in signatures or not self.data.startswith(signatures[self.mime]):
            raise WearableError('INVALID_IMAGE')
        # Header validation only. A real gateway must decode and bound pixel dimensions.
        return self


@dataclass(frozen=True)
class Request:
    request_id: str
    operation: str = 'look'

    @classmethod
    def parse(cls, body):
        if (type(body) is not dict or set(body) != {'version', 'request_id', 'operation'}
                or type(body['version']) is not int or body['version'] != 1
                or body['operation'] != 'look'):
            raise WearableError('INVALID_MESSAGE')
        return cls(identifier(body['request_id']))


class WearableDevice(Protocol):
    device_id: str
    capabilities: frozenset
    connected: bool
    camera_state: str
    # Adapter-bound state publisher, same lifecycle contract across devices.
    states: object
    def stop_playback(self) -> None: ...
    async def capture_audio(self) -> Audio: ...
    async def capture_image(self) -> Image: ...
    async def play_audio(self, audio: Audio) -> None: ...
    def stream_camera(self) -> AsyncIterator[Image]: ...
    def get_device_state(self) -> dict: ...
    def get_battery_state(self) -> int | None: ...
    async def display_text(self, text: str) -> None: ...
    async def display_image(self, image: Image) -> None: ...
    async def display_status(self, state: str) -> None: ...
    def gestures(self) -> AsyncIterator[str]: ...
