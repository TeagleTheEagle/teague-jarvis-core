"""Explicit live acceptance harness. Uses the running Core, never starts App/Store.

Reports contain the selected test image's hash, answer text and timing, not credentials.
Output must be new. Run only with --live; playback additionally requires --play.
"""
import argparse
import asyncio
import datetime
import hashlib
import io
import json
from pathlib import Path
import time

from .config import Config
from .interaction import Interaction
from .local_device import LocalDevelopmentAdapter
from .real_core import RealCore


class ObservedCore(RealCore):
    def __init__(self, conversation):
        super().__init__()
        self.conversation = conversation
        self.calls = []

    def request(self, op, body):
        start = time.perf_counter()
        try:
            result = super().request(op, body)
            if op != 'events':
                self.calls.append({'operation': op, 'elapsed_ms': round((time.perf_counter()-start)*1000, 2), 'success': True})
            return result
        except Exception:
            self.calls.append({'operation': op, 'elapsed_ms': round((time.perf_counter()-start)*1000, 2), 'success': False})
            raise

    async def respond(self, text, image=None, conversation=None):
        return await super().respond(text, image, conversation or self.conversation)


class ObservedDevice(LocalDevelopmentAdapter):
    def __init__(self, image, play):
        super().__init__(image_path=image, play=play)
        self.camera_calls = 0
        self.output_info = {}

    async def capture_image(self):
        self.camera_calls += 1
        return await super().capture_image()

    async def play_audio(self, audio):
        self.output_info = {'bytes': len(audio.data), 'sha256': hashlib.sha256(audio.data).hexdigest(),
                            'mime': audio.mime, 'duration_seconds': None, 'audible_user_confirmation': 'PENDING'}
        try:
            import soundfile
            info = soundfile.info(io.BytesIO(audio.data))
            self.output_info['duration_seconds'] = info.duration
        except Exception:
            self.output_info['duration_note'] = 'Decoder measurement unavailable; see playback elapsed time.'
        await super().play_audio(audio)
        self.output_info['playback_function_returned'] = True
        self.output_info['playback_enabled'] = self.play


async def verify(args):
    report = {'checked_at': datetime.datetime.now().astimezone().isoformat(),
              'input': 'Typed question through virtual glasses; no microphone/end-of-speech measurement',
              'core': 'Existing running PC Core via loopback; no new App/Store', 'failure': None}
    device = ObservedDevice(args.image, args.play)
    clock = time.perf_counter()
    observed = []
    original_emit = device.states.emit
    def emit(state):
        original_emit(state)
        observed.append({'state': device.states.state.value, 'ms': round((time.perf_counter()-clock)*1000, 2)})
    device.states.emit = emit
    core = None
    try:
        core = ObservedCore('wearable-m4-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
        report['core_status_before'] = await asyncio.to_thread(core.request, 'status', {})
        if args.image:
            path = Path(args.image)
            report['image'] = {'filename': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                               'source': 'User-supplied real screenshot, not generated fixture'}
        await asyncio.to_thread(core.request, 'register', {'capabilities': ['camera', 'microphone', 'speakers'],
                                  'ready': ['camera', 'speakers'] if args.image else ['speakers'], 'simulated': True})
        device.connect()
        report['result'] = await Interaction(device, Config('real', 'real', 'fixture', 'real'), core).run(args.text)
        report['camera_calls'] = device.camera_calls
        report['audio'] = device.output_info
        report['provider_measurements'] = core.measurements
        report['tts_server_ms'] = core.tts_ms
        report['core_status_after'] = await asyncio.to_thread(core.request, 'status', {})
    except Exception as error:
        report['failure'] = getattr(error, 'code', type(error).__name__)
    finally:
        device.disconnect()
        if core:
            try:
                await asyncio.to_thread(core.request, 'disconnect', {})
                report['registry_after_disconnect'] = await asyncio.to_thread(core.request, 'registry', {})
            except Exception as error: report['cleanup_failure'] = getattr(error, 'code', type(error).__name__)
            report['requests'] = core.calls
        report['state_events'] = observed
        report['notes'] = ['Playback command acceptance does not prove acoustic onset or human audibility.',
                           'AI first token and separate vision/AI durations unavailable on buffered Core path.',
                           'No synthetic transcript or microphone latency is reported as measured speech.']
        with Path(args.output).open('x', encoding='utf-8') as output:
            json.dump(report, output, indent=2)
        print(json.dumps(report, indent=2))
    return int(bool(report.get('failure') or report.get('result', {}).get('error')))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--play', action='store_true')
    parser.add_argument('--image')
    parser.add_argument('--text', default='JARVIS, what am I looking at?')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    if not args.live: parser.error('--live is required')
    if Path(args.output).exists(): parser.error('Report already exists; choose a new output')
    return asyncio.run(verify(args))


if __name__ == '__main__': raise SystemExit(main())
