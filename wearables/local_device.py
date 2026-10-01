import asyncio
from pathlib import Path
from .mock_device import MockWearableAdapter
from .contracts import Audio, Image, WearableError
from .output import EncodedAudio, play_mp3


class LocalDevelopmentAdapter(MockWearableAdapter):
    """Virtual glasses with explicitly selected local image, PC mic and PC output."""
    def __init__(self,image_path=None,live_mic=False,play=False,on_audio_started=None):
        super().__init__('local-development')
        self.image_path=image_path;self.live_mic=live_mic;self.play=play
        self.on_audio_started=on_audio_started

    async def capture_image(self):
        self.check('camera')
        if not self.image_path:return await super().capture_image()
        path=Path(self.image_path)
        if path.stat().st_size>2*1024*1024:raise WearableError('IMAGE_TOO_LARGE')
        raw=path.read_bytes()
        return Image(raw,'image/png' if raw.startswith(b'\x89PNG') else 'image/jpeg').validate()

    async def capture_audio(self):
        self.check('microphone')
        if not self.live_mic:return await super().capture_audio()
        try:import sounddevice as sd
        except ImportError:raise WearableError('INSTALL_REQUIREMENTS_WEARABLES') from None
        # Explicit five-second recording; no wake word or background listening.
        try:
            recording=sd.rec(5*16000,samplerate=16000,channels=1,dtype='int16')
            await asyncio.to_thread(sd.wait)
            self.check('microphone')
            return Audio(recording.tobytes()).validate()
        except asyncio.CancelledError:
            sd.stop();raise
        except Exception:raise WearableError('MICROPHONE_UNAVAILABLE') from None

    async def play_audio(self,audio):
        self.check('speaker')
        if isinstance(audio,EncodedAudio):
            audio.validate()
            if self.play:await play_mp3(audio,self.on_audio_started)
            else:self.outputs=[audio]
        else:await super().play_audio(audio)
