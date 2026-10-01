"""In-process mock gateway orchestration; no network listener or desktop imports."""
import asyncio
from .contracts import Request, WearableError
from .states import State
from .timing import Timing


class Pipeline:
    def __init__(self, device, core, policy):
        self.device, self.core, self.policy = device, core, policy
        self.active = False
        self.seen = set()

    async def run(self, token, body):
        request = Request.parse(body)
        self.policy.check(token,self.device.device_id,request.operation)
        if self.active: raise WearableError('BUSY')
        if request.request_id in self.seen: raise WearableError('REPLAY')
        if len(self.seen)>=100: raise WearableError('SESSION_LIMIT')
        generation = self.device.states.begin(request.request_id)
        self.seen.add(request.request_id)
        self.active = True
        timing = Timing()

        def check():
            self.device.states.check(generation)
            self.policy.check(token,self.device.device_id,request.operation)

        async def call(awaitable):
            result = await asyncio.wait_for(awaitable, timeout=5)
            check()
            return result

        try:
            timing.mark('speech_started')
            audio = await call(self.device.capture_audio())
            timing.mark('speech_ended')
            self.device.states.move(State.THINKING,generation)
            timing.mark('transcription_started')
            text = await call(self.core.transcribe(audio))
            timing.mark('transcription_complete')
            self.device.states.move(State.LOOKING,generation)
            image = await call(self.device.capture_image())
            self.device.camera_state = 'ANALYSING'
            timing.mark('vision_started')
            answer = await call(self.core.describe(text,image))
            timing.mark('vision_complete')
            self.device.camera_state = 'OFF'
            self.device.states.move(State.THINKING,generation)
            timing.mark('TTS_started')
            output = await call(self.core.synthesize(answer))
            timing.mark('first_audio_ready')
            check()
            self.device.states.move(State.SPEAKING,generation)
            await call(self.device.play_audio(output))
            timing.mark('audio_sink_received')
            self.device.states.move(State.IDLE,generation)
            return {'simulated':True,'request_id':request.request_id,'answer':answer,
                    'output':'synthetic tone delivered to virtual speaker (not JARVIS TTS)', 'timing':timing.report()}
        except (WearableError, TimeoutError, ConnectionError) as error:
            code = error.code if isinstance(error,WearableError) else ('TIMEOUT' if isinstance(error,TimeoutError) else 'NETWORK_LOST')
            if generation == self.device.states.generation:
                self.device.states.move(State.ERROR,generation)
                self.device.states.cancel(offline=not self.device.connected)
            self.device.stop_playback()
            return {'simulated':True,'error':code,'timing':timing.report()}
        except asyncio.CancelledError:
            if generation == self.device.states.generation: self.device.states.cancel()
            self.device.stop_playback()
            raise
        except Exception:
            # Adapter bugs must not leave the device permanently THINKING.
            if generation == self.device.states.generation:
                self.device.states.move(State.ERROR,generation)
                self.device.states.cancel(offline=not self.device.connected)
            self.device.stop_playback()
            return {'simulated':True,'error':'INTERNAL_ERROR','timing':timing.report()}
        finally:
            self.active = False
            self.device.camera_state = 'OFF'
