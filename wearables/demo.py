"""Run: python -m wearables.demo [--interactive] [--play-tone]."""
import argparse
import asyncio
import io
import json
import sys
import uuid
import wave
from .contracts import WearableError
from .mock_device import MockWearableAdapter
from .mock_core import MockCore
from .pipeline import Pipeline
from .policy import Policy


def play_tone(audio):
    if sys.platform != 'win32':
        print('Optional audible tone is Windows-only; virtual speaker received PCM.')
        return
    import winsound
    stream = io.BytesIO()
    with wave.open(stream,'wb') as wav:
        wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(16000); wav.writeframes(audio.pcm)
    winsound.PlaySound(stream.getvalue(), winsound.SND_MEMORY)


async def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--interactive',action='store_true')
    parser.add_argument('--play-tone',action='store_true',help='Play a quiet synthetic test tone on Windows')
    args=parser.parse_args()
    device=MockWearableAdapter(display=True); device.connect()
    core=MockCore(); policy=Policy(); token=policy.issue(device.device_id)
    pipeline=Pipeline(device,core,policy)
    print('TEAGUE INDUSTRIES // JARVIS MOCK GLASSES\nDEVELOPMENT ONLY: synthetic media, canned response, no network or saved memory.')
    async def run():
        try:
            result=await pipeline.run(token,{'version':1,'request_id':uuid.uuid4().hex,'operation':'look'})
            print(json.dumps(result,indent=2))
            print('States:', ' -> '.join(e['state'] for e in device.states.events[-8:]))
            if args.play_tone and device.outputs: play_tone(device.outputs[-1])
        except WearableError as e: print('DEVELOPMENT MOCK:',e.code)
    if not args.interactive:
        await run(); return
    print('Commands: look, disconnect, connect, deny-camera, allow-camera, deny-mic, allow-mic, fail-ai, fail-network, fail-timeout, reset, revoke, pair, status, quit')
    while True:
        try: command=input('mock> ').strip().lower()
        except (EOFError,KeyboardInterrupt): break
        try:
            if command=='quit': break
            elif command=='look': await run()
            elif command=='disconnect': device.disconnect()
            elif command=='connect': device.connect()
            elif command in ('deny-camera','allow-camera'): device.permissions['camera']=command.startswith('allow')
            elif command in ('deny-mic','allow-mic'): device.permissions['microphone']=command.startswith('allow')
            elif command.startswith('fail-'): core.fault={'fail-ai':'vision','fail-network':'network','fail-timeout':'timeout'}.get(command)
            elif command=='reset': core.fault=None; device.permissions.update(camera=True,microphone=True)
            elif command=='revoke': policy.revoke(token)
            elif command=='pair':
                policy.revoke(token); token=policy.issue(device.device_id); pipeline=Pipeline(device,core,policy)
            elif command=='status': print(json.dumps({**device.get_device_state(),'simulated_battery':device.get_battery_state()}))
            else: print('Unknown command. Use look or status.')
        except WearableError as e: print(e.code)
    device.disconnect()


if __name__=='__main__': asyncio.run(main())
