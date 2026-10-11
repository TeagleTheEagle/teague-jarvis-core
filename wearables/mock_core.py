"""Explicit development provider. No AI keys, database, network or personality copy."""
import asyncio
from .contracts import WearableError
from .mock_device import tone


class MockCore:
    def __init__(self, fault=None):
        self.fault = fault

    async def stage(self, name):
        await asyncio.sleep(0)
        if self.fault == name: raise WearableError('AI_SERVICE_UNAVAILABLE')
        if self.fault == 'timeout': raise TimeoutError()
        if self.fault == 'network': raise ConnectionError()

    async def transcribe(self, audio):
        audio.validate(); await self.stage('stt')
        return 'JARVIS, what am I looking at?'

    async def describe(self, text, image):
        image.validate(); await self.stage('vision')
        return 'DEVELOPMENT MOCK: Camera fixture received, sir. Real scene analysis is not enabled.'

    async def respond(self, text, image=None):
        if image:return await self.describe(text,image)
        await self.stage('text')
        return 'DEVELOPMENT MOCK: Text received. No real JARVIS inference was requested.'

    async def synthesize(self, text):
        await self.stage('tts')
        return tone()
