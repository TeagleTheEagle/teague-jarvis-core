"""Explicit live-service validation in temporary storage. Never starts the desktop.

Run only with --live. Uses existing server configuration, synthetic image, and
existing saved voice profile; reports no keys or provider exception bodies.
"""
import argparse
import asyncio
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
from PIL import Image
from .config import Config
from .interaction import Interaction
from .local_device import LocalDevelopmentAdapter
from .real_core import RealCore
from .service import Service
from .contracts import WearableError


async def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--live',action='store_true');args=parser.parse_args()
    if not args.live:parser.error('Explicit --live is required for provider requests.')
    from server import App,Server,Handler
    from store import VOICE_PROFILES
    root=Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix='jarvis-wearable-probe-') as folder:
        app=App(Path(folder)/'data')
        # Read only the voice profile; leave personal data and live database untouched.
        db=sqlite3.connect((root/'data/jarvis.sqlite3').as_uri()+'?mode=ro',uri=True)
        try:row=db.execute("SELECT value FROM settings WHERE key='voice_profile'").fetchone()
        finally:db.close()
        if row and json.loads(row[0]) in VOICE_PROFILES:app.store.save_settings({'voice_profile':json.loads(row[0])})  # an old ElevenLabs choice stays automatic
        server=Server(('127.0.0.1',0),Handler);server.app=app;server.wearable_service=Service(app)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            core=RealCore({'url':f'http://127.0.0.1:{server.server_port}','token':server.wearable_service.token})
            image=Path(folder)/'synthetic.png';Image.new('RGB',(64,64),'blue').save(image)
            device=LocalDevelopmentAdapter(image);device.connect()
            result=await Interaction(device,Config('real','real','fixture','real'),core).run('JARVIS, what am I looking at?')
            result['probe']='isolated temporary conversation, synthetic blue image, real configured services, virtual speaker'
            # If AI quota blocks the turn, independently verify TTS with harmless fixed text.
            if 'error' in result:
                try:
                    audio=await core.synthesize('Voice connection checked, sir.')
                    result['independent_voice']={'status':'audio_generated','bytes':len(audio.data),'tts_ms':core.tts_ms}
                except WearableError as e:result['independent_voice']={'error':e.code}
            print(json.dumps(result,indent=2))
        finally:server.shutdown();server.server_close();thread.join()


if __name__=='__main__':asyncio.run(main())
