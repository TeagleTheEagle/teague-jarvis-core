import asyncio
import unittest
from unittest.mock import patch
from wearables.mock_device import MockWearableAdapter
from wearables.mock_core import MockCore
from wearables.pipeline import Pipeline
from wearables.policy import Policy
from wearables.contracts import WearableError, Audio


class MockTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.device=MockWearableAdapter(); self.device.connect()
        self.policy=Policy(); self.token=self.policy.issue(self.device.device_id)
        self.core=MockCore(); self.pipeline=Pipeline(self.device,self.core,self.policy)

    async def run_turn(self, ident='turn'):
        return await self.pipeline.run(self.token,{'version':1,'request_id':ident,'operation':'look'})

    async def test_complete_loop(self):
        with patch('socket.create_connection',side_effect=AssertionError('No network allowed')):
            result=await self.run_turn()
        self.assertTrue(result['simulated']); self.assertIn('DEVELOPMENT MOCK',result['answer'])
        self.assertEqual(len(self.device.outputs),1)
        self.assertEqual(self.device.get_device_state()['state'],'IDLE')
        self.assertEqual(self.device.camera_state,'OFF')
        self.assertIsNone(result['timing']['AI_first_token_ms'])
        with self.assertRaises(WearableError): await self.run_turn()

    async def test_permissions_and_malformed_media(self):
        for index,permission in enumerate(('microphone','camera','speaker')):
            self.device.permissions[permission]=False
            result=await self.run_turn('denied-'+str(index))
            self.assertEqual(result['error'],'PERMISSION_DENIED'); self.assertFalse(self.device.outputs)
            self.device.permissions[permission]=True
        self.device.audio=Audio(b'bad')
        self.assertEqual((await self.run_turn('bad'))['error'],'INVALID_AUDIO')

    async def test_failures_recover(self):
        for fault,code in [('vision','AI_SERVICE_UNAVAILABLE'),('tts','AI_SERVICE_UNAVAILABLE'),('timeout','TIMEOUT'),('network','NETWORK_LOST')]:
            self.core.fault=fault
            self.assertEqual((await self.run_turn(fault))['error'],code)
            self.assertEqual(self.device.get_device_state()['state'],'IDLE')
        self.core.fault=None
        self.assertIn('answer',await self.run_turn('recovery'))

    async def test_disconnect_and_reconnect_mid_turn(self):
        original=self.core.describe
        async def interrupt(text,image):
            self.device.disconnect(); self.device.connect()
            return await original(text,image)
        self.core.describe=interrupt
        self.assertEqual((await self.run_turn())['error'],'CANCELLED')
        self.assertFalse(self.device.outputs)
        self.core.describe=original
        self.assertIn('answer',await self.run_turn('new'))

    async def test_revoke_mid_turn(self):
        original=self.core.synthesize
        async def revoke(text):
            self.policy.revoke(self.token)
            return await original(text)
        self.core.synthesize=revoke
        self.assertEqual((await self.run_turn())['error'],'UNAUTHENTICATED')
        self.assertFalse(self.device.outputs)

    async def test_busy_and_cancel(self):
        gate=asyncio.Event()
        async def wait(audio): await gate.wait(); return 'fixture'
        self.core.transcribe=wait
        pending=asyncio.create_task(self.run_turn())
        await asyncio.sleep(0)
        with self.assertRaises(WearableError): await self.run_turn('second')
        pending.cancel()
        with self.assertRaises(asyncio.CancelledError): await pending
        self.assertFalse(self.pipeline.active); self.assertFalse(self.device.outputs)

    async def test_stream_display_gestures(self):
        frames=[frame async for frame in self.device.stream_camera()]
        self.assertEqual(len(frames),3)
        with self.assertRaises(WearableError): await self.device.display_text('test')
        self.device.inject_gesture('tap')
        self.assertEqual([g async for g in self.device.gestures()],['tap'])
        display=MockWearableAdapter(display=True); display.connect()
        await display.display_status('THINKING')
        self.assertTrue(display.display_output['simulated'])

    async def test_offline_and_device_fault(self):
        self.device.disconnect()
        with self.assertRaises(WearableError): await self.run_turn()
        self.device.connect(); self.device.fault='camera'
        self.assertEqual((await self.run_turn('fault'))['error'],'DEVICE_ERROR')

    async def test_unexpected_adapter_error_resets_state(self):
        async def broken(audio): raise RuntimeError('private implementation detail')
        self.core.transcribe=broken
        result=await self.run_turn()
        self.assertEqual(result['error'],'INTERNAL_ERROR')
        self.assertNotIn('private',str(result))
        self.assertEqual(self.device.get_device_state()['state'],'IDLE')

    async def test_state_subscription_is_bounded_and_closes(self):
        stream=self.device.states.subscribe()
        self.assertEqual((await anext(stream))['state'],'IDLE')
        await self.run_turn()
        self.assertEqual((await anext(stream))['state'],'IDLE')
        await stream.aclose()
        self.assertFalse(self.device.states._subscribers)

    async def test_camera_stream_rechecks_permission(self):
        stream=self.device.stream_camera()
        await anext(stream)
        self.device.permissions['camera']=False
        with self.assertRaises(WearableError): await anext(stream)
