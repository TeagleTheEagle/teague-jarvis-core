"""Milestone 4 explicit mixed-mode demo. Defaults remain entirely offline."""
import argparse
import asyncio
import json
from .config import Config
from .contracts import WearableError
from .local_device import LocalDevelopmentAdapter
from .interaction import Interaction


async def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ai',choices=['mock','real']);parser.add_argument('--vision',choices=['mock','real'])
    parser.add_argument('--voice',choices=['mock','real']);parser.add_argument('--mic',choices=['fixture','live'])
    parser.add_argument('--image');parser.add_argument('--text');parser.add_argument('--play',action='store_true')
    args=parser.parse_args()
    try:
        default=Config.from_env()
        config=Config(args.ai or default.ai,args.voice or default.voice,args.mic or default.mic,args.vision or default.vision).validate()
        if config.vision=='real' and not args.image:raise WearableError('PROVIDE_LOCAL_IMAGE_FOR_REAL_VISION')
        real=None
        if 'real' in (config.ai,config.voice,config.vision) or config.mic=='live':
            from .real_core import RealCore
            real=RealCore()
        device=LocalDevelopmentAdapter(args.image,config.mic=='live',args.play);device.connect()
        if config.mic=='live' and args.text is None:print('Recording PC microphone for five seconds. Speak now.')
        print('TEAGUE INDUSTRIES // MILESTONE 4\nModes:',config.__dict__)
        print('Real modes send input to the running PC JARVIS; its configured AI/voice services may receive content. Conversations use existing saved history.')
        result=await Interaction(device,config,real).run(args.text)
        print(json.dumps(result,indent=2));print('States:', ' -> '.join(e['state'] for e in device.states.events))
        device.disconnect()
        return 1 if 'error' in result else 0
    except WearableError as error:print(error.code);return 1


if __name__=='__main__':raise SystemExit(asyncio.run(main()))
