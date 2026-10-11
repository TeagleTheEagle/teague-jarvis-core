import unittest
from device_registry import DeviceRegistry


class RegistryTests(unittest.TestCase):
    def test_cooperation_one_request(self):
        registry=DeviceRegistry();registry.register('glasses',{'camera','microphone','speakers'},ready={'camera','microphone','speakers'})
        registry.register('pc',{'display'},ready={'display'});registry.begin('request-1','glasses')
        plan=registry.plan('request-1',{'vision':'camera','output':'display','voice':'speakers'})
        self.assertTrue(plan['cooperation']);self.assertFalse(plan['executable'])
        self.assertEqual([s['device_id'] for s in plan['steps']],['glasses','pc','glasses'])
        self.assertEqual(plan['interaction_device'],'glasses')

    def test_expired_permissions_and_simulation(self):
        now=[0];r=DeviceRegistry(lambda:now[0]);r.register('mock',{'display'},ready={'display'},ttl=1,simulated=True)
        self.assertIsNone(r.plan('x',{'out':'display'})['steps'][0]['device_id'])
        self.assertEqual(r.plan('x',{'out':'display'},allow_simulated=True)['steps'][0]['device_id'],'mock')
        now[0]=2;self.assertFalse(r.snapshot()[0]['connected'])
        self.assertIsNone(r.plan('x',{'out':'display'},allow_simulated=True)['steps'][0]['device_id'])
        with self.assertRaises(ValueError):r.register('x',{'camera'},ready={'shell'})

    def test_disconnect_clears_active_request(self):
        r=DeviceRegistry();r.register('phone',{'camera'});r.begin('a','phone');r.disconnect('phone')
        self.assertIsNone(r.interaction('a'))
        self.assertIsNone(r.plan('a',{'vision':'camera'})['steps'][0]['device_id'])
