"""Devices the right way round (release 1.0.15, scope item 4; master document sections 5 and 19).

The device book: a device has a name, a kind and its own key; it pairs with a code the owner reads from the
PC; what it declares is not what it may use; the owner can take a capability or the whole device back at any time.
"""
import re
import tempfile
import unittest
from pathlib import Path

import devices
from devices import DeviceBook, DeviceError
from store import Store


class DeviceBookTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.now = [1000.0]
        self.store = Store(self.root / 'data')
        self.book = DeviceBook(self.store, self.root / 'config', clock=lambda: self.now[0])

    def pair(self, name='Phone', kind='phone', declared=('microphone', 'camera')):
        code = self.book.begin_pairing(name, kind)['code']
        return self.book.finish_pairing(code, list(declared))

    def test_pairing_gives_the_device_its_own_key_once(self):
        started = self.book.begin_pairing(' My phone ', 'phone')
        self.assertRegex(started['code'], r'^\d{4} \d{4}$')
        self.assertEqual((started['name'], started['kind'], started['expires']), ('My phone', 'phone', 1300.0))
        self.assertEqual(self.book.pairing(), {'name': 'My phone', 'kind': 'phone', 'expires': 1300.0})  # never the code
        paired = self.book.finish_pairing(started['code'], ['camera', 'microphone'])
        self.assertRegex(paired['device_id'], r'^[a-f0-9]{16}$')
        self.assertEqual(paired['credential'], paired['device_id'] + '.' + paired['key'])
        self.assertEqual(paired['allowed'], ['microphone', 'camera'])
        self.assertIsNone(self.book.pairing())
        with self.assertRaises(DeviceError):  # the code works once
            self.book.finish_pairing(started['code'], [])
        device = self.book.authenticate(paired['credential'])
        self.assertEqual((device['name'], device['kind'], device['declared'], device['allowed'], device['key_valid']),
                         ('My phone', 'phone', ['microphone', 'camera'], ['microphone', 'camera'], True))
        # Nothing that could be used as a key is stored: not the key, not a plain hash of it.
        with self.store.connect() as db:
            stored = dict(db.execute('SELECT * FROM devices').fetchone())
        self.assertNotIn(paired['key'], str(stored))
        import hashlib
        self.assertNotEqual(stored['key_hash'], hashlib.sha256(paired['key'].encode()).hexdigest())
        self.assertNotIn('key_hash', device)

    def test_a_wrong_expired_or_missing_code_pairs_nothing(self):
        with self.assertRaises(DeviceError): self.book.finish_pairing('1234 5678', [])  # nothing waiting
        code = self.book.begin_pairing('Phone', 'phone')['code']
        wrong = '0000 0000' if code != '0000 0000' else '1111 1111'
        for _ in range(devices.PAIRING_ATTEMPTS - 1):
            with self.assertRaises(DeviceError): self.book.finish_pairing(wrong, [])
        self.assertIsNotNone(self.book.pairing())
        with self.assertRaises(devices.WrongCode): self.book.finish_pairing(wrong, [])  # the last wrong code in all ends the pairing (per caller: device_gateway.py)
        self.assertIsNone(self.book.pairing())
        with self.assertRaises(DeviceError): self.book.finish_pairing(code, [])  # even the right code is now too late
        code = self.book.begin_pairing('Phone', 'phone')['code']
        self.now[0] += devices.PAIRING_SECONDS + 1
        with self.assertRaises(DeviceError): self.book.finish_pairing(code, [])
        code = self.book.begin_pairing('Phone', 'phone')['code']
        self.book.cancel_pairing()
        with self.assertRaises(DeviceError): self.book.finish_pairing(code, [])
        for bad in (None, 12345678, '', '1234', 'abcd efgh', code + '9'):
            self.book.begin_pairing('Phone', 'phone')
            with self.assertRaises(DeviceError): self.book.finish_pairing(bad, [])
        self.assertEqual(self.book.list(), [])
        # A new pairing replaces the one that was waiting: the old code is dead.
        old = self.book.begin_pairing('Phone', 'phone')['code']
        new = self.book.begin_pairing('Glasses', 'glasses')['code']
        if old != new:
            with self.assertRaises(DeviceError): self.book.finish_pairing(old, [])
            new = self.book.begin_pairing('Glasses', 'glasses')['code']
        self.assertEqual(self.book.finish_pairing(new, [])['kind'], 'glasses')

    def test_names_kinds_and_capabilities_are_checked(self):
        for name, kind in (('', 'phone'), ('x' * 61, 'phone'), (None, 'phone'), ('<b>x</b>', 'phone'), ('Phone', 'pc'), ('Phone', 'tank'), ('Phone', None)):
            with self.assertRaises(DeviceError): self.book.begin_pairing(name, kind)
        code = self.book.begin_pairing('Phone', 'phone')['code']
        for declared in (['shell'], ['camera', 'files'], 'camera', None):
            with self.assertRaises(DeviceError): self.book.finish_pairing(code, declared)
        self.assertEqual(self.book.finish_pairing(code, ['display', 'camera', 'camera'])['allowed'], ['camera', 'display'])

    def test_only_the_right_key_of_a_device_that_is_not_revoked_is_accepted(self):
        phone, glasses = self.pair('Phone'), self.pair('Halo', 'glasses')
        for bad in (None, '', 'pc', phone['device_id'], phone['device_id'] + '.', phone['device_id'] + '.' + glasses['key'],
                    glasses['device_id'] + '.' + phone['key'], '0' * 16 + '.' + phone['key'], phone['credential'] + 'x', ' ' + phone['credential']):
            with self.assertRaises(PermissionError): self.book.authenticate(bad)
        self.assertEqual(self.book.authenticate(glasses['credential'])['name'], 'Halo')
        self.now[0] += 50
        revoked = self.book.revoke(phone['device_id'])
        self.assertEqual((revoked['revoked'], revoked['allowed'], revoked['key_valid']), (1050.0, [], False))
        with self.assertRaises(PermissionError): self.book.authenticate(phone['credential'])
        self.assertEqual(self.book.authenticate(glasses['credential'])['name'], 'Halo')  # the other device is untouched
        self.assertEqual(self.book.revoke(phone['device_id'])['revoked'], 1050.0)  # revoking twice changes nothing
        with self.assertRaises(DeviceError): self.book.allow(phone['device_id'], [])
        with self.assertRaises(DeviceError): self.book.forget(glasses['device_id'])  # only a revoked device is forgotten
        self.assertEqual(self.book.forget(phone['device_id']), {'forgotten': phone['device_id']})
        self.assertEqual([d['name'] for d in self.book.list()], ['Halo'])
        for missing in (self.book.revoke, self.book.forget, self.book.get):
            with self.assertRaises(DeviceError): missing('f' * 16)

    def test_what_a_device_declares_is_not_what_it_may_use(self):
        phone = self.pair(declared=('microphone',))
        ident = phone['device_id']
        self.assertEqual(self.book.allow(ident, [])['allowed'], [])            # the owner takes the microphone back
        self.assertEqual(self.book.get(ident)['declared'], ['microphone'])
        with self.assertRaises(DeviceError): self.book.allow(ident, ['camera'])  # not declared: cannot be allowed
        # Later the device says it also has a camera: that is noted, and not allowed by itself.
        self.assertEqual(self.book.declare(ident, ['microphone', 'camera']), {'declared': ['microphone', 'camera'], 'allowed': []})
        self.assertEqual(self.book.allow(ident, ['camera', 'microphone'])['allowed'], ['microphone', 'camera'])
        # It stops declaring the microphone: that permission goes with it.
        self.assertEqual(self.book.declare(ident, ['camera']), {'declared': ['camera'], 'allowed': ['camera']})
        with self.assertRaises(DeviceError): self.book.declare(ident, ['root'])
        self.book.revoke(ident)
        with self.assertRaises(PermissionError): self.book.declare(ident, ['camera'])

    def test_devices_survive_a_restart_and_keys_do_not_survive_a_move_to_another_installation(self):
        phone = self.pair('Phone')
        again = DeviceBook(Store(self.root / 'data'), self.root / 'config', clock=lambda: self.now[0])
        self.assertEqual(again.authenticate(phone['credential'])['name'], 'Phone')
        self.assertEqual(again.rename(phone['device_id'], 'Work phone')['name'], 'Work phone')
        self.assertEqual(again.names(), {phone['device_id']: 'Work phone'})
        # The same database beside another installation's config folder (a restored backup): the list is there,
        # the key is not accepted, and the panel can say why.
        moved = DeviceBook(Store(self.root / 'data'), self.root / 'other-config', clock=lambda: self.now[0])
        self.assertEqual([(d['name'], d['key_valid']) for d in moved.list()], [('Work phone', False)])
        with self.assertRaises(PermissionError): moved.authenticate(phone['credential'])
        self.assertFalse((self.root / 'other-config' / devices.SECRET_FILE).exists())  # looking makes no secret
        fresh = moved.finish_pairing(moved.begin_pairing('New phone', 'phone')['code'], [])
        self.assertTrue(moved.authenticate(fresh['credential'])['key_valid'])
        with self.assertRaises(PermissionError): moved.authenticate(phone['credential'])
        # The secret is a private file name that backups and git leave out.
        self.assertTrue(devices.SECRET_FILE.startswith('.env'))
        self.assertTrue(re.fullmatch(r'[a-f0-9]{64}\n', (self.root / 'config' / devices.SECRET_FILE).read_text()))

    def test_the_owners_tick_may_save_memories_and_tasks_is_off_until_ticked_and_goes_with_a_revoke(self):
        phone = self.pair('Phone')
        ident = phone['device_id']
        self.assertFalse(phone['writes'])
        self.assertFalse(self.book.authenticate(phone['credential'])['writes'])
        self.assertTrue(self.book.set_writes(ident, True)['writes'])
        self.assertTrue(self.book.authenticate(phone['credential'])['writes'])
        self.assertFalse(self.book.set_writes(ident, False)['writes'])
        with self.assertRaises(DeviceError): self.book.set_writes(ident, 'yes')
        with self.assertRaises(DeviceError): self.book.set_writes('f' * 16, True)
        self.book.set_writes(ident, True)
        self.book.revoke(ident)
        self.assertFalse(self.book.get(ident)['writes'])
        with self.assertRaises(DeviceError): self.book.set_writes(ident, True)
        # A database from 1.0.15 (no column yet) is brought up to date, with the tick off for every device.
        with self.store.connect() as db:
            self.assertIn('writes', {row[1] for row in db.execute('PRAGMA table_info(devices)')})

    def test_there_is_a_limit_and_last_seen_is_kept(self):
        phone = self.pair('Phone')
        self.now[0] += 30
        self.book.seen(phone['device_id'])
        self.assertEqual(self.book.get(phone['device_id'])['last_seen'], 1030.0)
        for index in range(devices.MAX_DEVICES - 1):
            self.pair(f'Device {index}', 'other', ())
        with self.assertRaises(DeviceError): self.book.begin_pairing('One too many', 'phone')
        self.book.revoke(phone['device_id'])  # a revoked device does not count
        self.assertEqual(self.pair('Replacement')['name'], 'Replacement')


if __name__ == '__main__':
    unittest.main()
