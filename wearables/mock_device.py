"""Deterministic virtual sensors and output sink. No hardware access."""
import asyncio
import base64
import math
import struct
from .contracts import Audio, Image, WearableError, identifier
from .states import StateMachine


def tone():
    # 0.2 seconds, quiet synthetic tone; never represented as synthesized speech.
    return Audio(b''.join(struct.pack('<h', int(1500*math.sin(2*math.pi*440*i/16000))) for i in range(3200)))


def fixture_image():
    # Synthetic one-pixel PNG. Mock answer never claims to recognize it.
    return Image(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a9ioAAAAASUVORK5CYII='), 'image/png')


class MockWearableAdapter:
    def __init__(self, device_id='mock-glasses', display=False):
        self.device_id = identifier(device_id)
        self.capabilities = frozenset({'microphone','camera','speaker','gestures'} | ({'display'} if display else set()))
        self.permissions = {'microphone':True, 'camera':True, 'speaker':True, 'display':True, 'gestures':True}
        self.states = StateMachine(device_id)
        self.connected = False
        self.battery = 80
        self.camera_state = 'OFF'
        self.outputs = []
        self.display_output = None
        self.fault = None
        self.audio = tone()
        self.image = fixture_image()
        self._gestures = asyncio.Queue(maxsize=8)

    def connect(self):
        if self.connected:
            raise WearableError('ALREADY_CONNECTED')
        self.connected = True
        self.states.connect()

    def disconnect(self):
        self.connected = False
        self.camera_state = 'OFF'
        self.states.cancel(offline=True)
        self.outputs.clear()
        self.display_output = None

    def stop_playback(self):
        self.outputs.clear()

    def check(self, capability):
        if not self.connected: raise WearableError('OFFLINE')
        if capability not in self.capabilities: raise WearableError('UNSUPPORTED')
        if not self.permissions.get(capability): raise WearableError('PERMISSION_DENIED')
        if self.fault == capability: raise WearableError('DEVICE_ERROR')

    async def capture_audio(self):
        self.check('microphone')
        return self.audio.validate()

    async def capture_image(self):
        self.check('camera')
        self.camera_state = 'READY'
        self.camera_state = 'CAPTURING'
        try: return self.image.validate()
        except WearableError:
            self.camera_state = 'ERROR'
            raise
        finally:
            if self.camera_state != 'ERROR': self.camera_state = 'OFF'

    async def play_audio(self, audio):
        self.check('speaker')
        self.outputs.append(audio.validate())
        self.outputs = self.outputs[-1:]

    async def stream_camera(self):
        # Explicit finite fixture stream; recheck connection and permission each frame.
        generation = self.states.generation
        for _ in range(3):
            await asyncio.sleep(0)
            self.states.check(generation)
            yield await self.capture_image()

    def get_device_state(self):
        return {'simulated':True, 'connected':self.connected, 'state':self.states.state.value,
                'camera':self.camera_state, 'capabilities':sorted(self.capabilities)}

    def get_battery_state(self):
        return self.battery if self.connected else None

    async def display_text(self, text):
        self.check('display')
        if not isinstance(text,str) or len(text)>500: raise WearableError('INVALID_DISPLAY')
        self.display_output = {'simulated':True, 'text':text}

    async def display_image(self, image):
        self.check('display'); self.display_output = image.validate()

    async def display_status(self, state):
        await self.display_text(state)

    def inject_gesture(self, gesture):
        self.check('gestures')
        if gesture not in {'tap','hold'}: raise WearableError('INVALID_GESTURE')
        try: self._gestures.put_nowait(gesture)
        except asyncio.QueueFull: raise WearableError('BUSY') from None

    async def gestures(self):
        while not self._gestures.empty():
            self.check('gestures')
            yield self._gestures.get_nowait()
