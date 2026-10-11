import unittest
from wearables.contracts import Audio, Image, Request, WearableError
from wearables.states import StateMachine, State
from wearables.policy import Policy


class Contracts(unittest.TestCase):
    def test_media_bounds(self):
        Audio(bytes(3200)).validate()
        for audio in (Audio(b'x'), Audio(bytes(3200), 48000), Audio(bytes(960002)), Audio(bytes(3201))):
            with self.assertRaises(WearableError): audio.validate()
        for image in (Image(b'not an image', 'image/png'), Image(bytes(2097153), 'image/png')):
            with self.assertRaises(WearableError): image.validate()

    def test_envelope(self):
        valid = {'version': 1, 'request_id': 'turn-1', 'operation': 'look'}
        self.assertEqual(Request.parse(valid).operation, 'look')
        for change in ({'device_id':'forged'}, {'version':True}, {'operation':'shell'}, {'request_id':'../escape'}):
            with self.assertRaises(WearableError): Request.parse({**valid, **change})

    def test_scopes_expiry_and_revocation(self):
        now = [0]; p = Policy(lambda: now[0]); key = p.issue('glasses')
        p.check(key, 'glasses', 'look')
        for device, op in [('desktop','look'), ('glasses','shell')]:
            with self.assertRaises(WearableError): p.check(key, device, op)
        now[0] = 301
        with self.assertRaises(WearableError): p.check(key, 'glasses', 'look')
        key = p.issue('glasses'); p.revoke(key)
        with self.assertRaises(WearableError): p.check(key, 'glasses', 'look')

    def test_stale_state_and_transitions(self):
        s = StateMachine('glasses'); s.connect(); g = s.begin('turn')
        with self.assertRaises(WearableError): s.move(State.SPEAKING,g)
        s.cancel(offline=True); s.connect()
        with self.assertRaises(WearableError): s.move(State.THINKING,g)
        self.assertEqual(s.state, State.IDLE)
        self.assertEqual([e['sequence'] for e in s.events], list(range(len(s.events))))

    def test_all_shared_states(self):
        self.assertEqual({s.value for s in State}, {'OFFLINE','IDLE','LISTENING','THINKING','LOOKING','SPEAKING','EXECUTING','ERROR'})
