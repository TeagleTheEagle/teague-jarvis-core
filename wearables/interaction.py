"""Mode routing and truthful local timing; production core is injected."""
import time
import asyncio
import uuid
from .intent import needs_camera
from .states import State
from .contracts import WearableError
from .mock_core import MockCore


class Interaction:
    def __init__(self,device,config,real=None):
        self.device=device;self.config=config.validate();self.real=real;self.mock=MockCore()

    async def run(self,text=None):
        device=self.device;generation=device.states.begin(uuid.uuid4().hex)
        started=time.perf_counter();marks={};answer=None
        def mark(name):marks[name]=round((time.perf_counter()-started)*1000,2)
        device.on_audio_started=lambda:mark('playback_command_accepted')
        async def call(awaitable):
            result=await awaitable;device.states.check(generation);return result
        try:
            if text is None:
                mark('capture_started');audio=await call(device.capture_audio());mark('capture_complete')
                mark('stt_started')
                text=await call((self.real if self.config.mic=='live' else self.mock).transcribe(audio));mark('stt_complete')
            if not isinstance(text,str) or not text.strip():raise WearableError('NO_SPEECH')
            device.states.move(State.THINKING,generation)
            mark('intent_started');image=None;visual=needs_camera(text);mark('intent_complete')
            if visual:
                device.states.move(State.LOOKING,generation)
                mark('camera_started');image=await call(device.capture_image());mark('camera_complete')
                device.states.move(State.THINKING,generation)
            mark('core_started')
            if visual and self.config.vision=='mock':
                answer=await call(self.mock.describe(text,image))
            elif self.config.ai=='real':
                answer=await call(self.real.respond(text,image))
            else:answer=await call(self.mock.respond(text))
            mark('core_complete');mark('tts_started')
            output=await call((self.real if self.config.voice=='real' else self.mock).synthesize(answer));mark('first_audio_ready')
            device.states.move(State.SPEAKING,generation)
            await call(device.play_audio(output));mark('output_complete')
            device.states.move(State.IDLE,generation)
            status={'answer':answer,'camera_used':visual,'answer_source':'real' if self.config.ai=='real' and (not visual or self.config.vision=='real') else 'mock'}
        except asyncio.CancelledError:
            if generation==device.states.generation:device.states.cancel(offline=not device.connected)
            device.stop_playback()
            raise
        except Exception as error:
            if generation==device.states.generation:
                device.states.move(State.ERROR,generation);device.states.cancel(offline=not device.connected)
            device.stop_playback()
            status={'error':error.code if isinstance(error,WearableError) else 'INTERACTION_FAILED'}
            if answer:status['answer']=answer  # TTS failure never loses the successful text answer.
        finally:device.camera_state='OFF'
        mark('finished')
        def duration(a,b):return round(marks[b]-marks[a],2) if a in marks and b in marks else None
        status['modes']=self.config.__dict__
        status['events_ms']=dict(marks)
        status['latency_ms']={'capture':duration('capture_started','capture_complete'),'speech_to_text':duration('stt_started','stt_complete'),
            'intent_routing':duration('intent_started','intent_complete'),
            'camera_capture':duration('camera_started','camera_complete'),'core_including_vision':duration('core_started','core_complete'),
            'vision_separate':None,'AI_first_token':None,'tts_to_complete_audio':duration('tts_started','first_audio_ready'),
            'total_to_audio_ready':marks.get('first_audio_ready'),'total_to_playback_command':marks.get('playback_command_accepted'),
            'audio_startup':duration('first_audio_ready','playback_command_accepted'),
            'playback_command_to_complete':duration('playback_command_accepted','output_complete'),
            'total_response':marks['finished']}
        status['timing_note']='Same-PC monotonic timings. Playback command is not measured acoustic onset. Vision is included in Core; first-token unavailable for buffered responses.'
        if self.real and getattr(self.real,'last_failure',None):status['service_diagnostic']=self.real.last_failure
        return status
