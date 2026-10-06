"""Item H (docs/PHONE-ACCESS-1.0.17.md section 7): the devices this PC has seen on the home network, read passively from
Windows' neighbour table (faked here: no PowerShell, no network), named only through this PC's DNS server (faked, and the
scripts pinned to the boundary), cached a minute; the tool for a question and for a paired device; the owner's route; the
plain refusal."""
import json
import os
import re
import subprocess
import unittest
from unittest.mock import patch

import network_devices
import providers
from server import Run
from test_device_gateway import DONE, ENV, DeviceCase, calls

TABLE = {'neighbours': [
    {'IPAddress': '192.168.1.1', 'LinkLayerAddress': 'AA-BB-CC-00-11-22', 'State': 'Reachable', 'InterfaceAlias': 'Wi-Fi'},
    {'IPAddress': '192.168.1.42', 'LinkLayerAddress': 'aa:bb:cc:dd:ee:ff', 'State': 4, 'InterfaceAlias': 'Wi-Fi'},        # the state as a number, the address with colons
    {'IPAddress': '192.168.1.255', 'LinkLayerAddress': 'FF-FF-FF-FF-FF-FF', 'State': 'Permanent', 'InterfaceAlias': 'Wi-Fi'},   # broadcast
    {'IPAddress': '224.0.0.251', 'LinkLayerAddress': '01-00-5E-00-00-FB', 'State': 'Permanent', 'InterfaceAlias': 'Wi-Fi'},     # multicast
    {'IPAddress': '192.168.1.77', 'LinkLayerAddress': '00-00-00-00-00-00', 'State': 'Unreachable', 'InterfaceAlias': 'Wi-Fi'},  # nothing there
    {'IPAddress': '192.168.1.9', 'LinkLayerAddress': 'DE-AD-BE-EF-00-01', 'State': 'Incomplete', 'InterfaceAlias': 'Wi-Fi'},   # never answered
    {'IPAddress': '169.254.3.4', 'LinkLayerAddress': 'DE-AD-BE-EF-00-02', 'State': 'Reachable', 'InterfaceAlias': 'Ethernet'},  # link-local
    {'IPAddress': '192.168.1.20', 'LinkLayerAddress': 'DE-AD-BE-EF-00-03', 'State': 'Reachable', 'InterfaceAlias': 'Wi-Fi'},   # this PC itself
], 'mine': [{'IPAddress': '192.168.1.20', 'InterfaceAlias': 'Wi-Fi'}, {'IPAddress': '127.0.0.1', 'InterfaceAlias': 'Loopback'}], 'computer': 'THEGRIZZLYBEAR'}
DNS = {'192.168.1.1': 'router.home', '192.168.1.42': 'printer.home.'}   # as DNS writes a name, with its trailing dot
NAMES = {'192.168.1.1': 'router.home', '192.168.1.42': 'printer.home'}


def quoted(script):
    return re.findall(r"'(\d+\.\d+\.\d+\.\d+)'", script)


def fake_run(script):
    """Windows, faked: the table for the neighbour script, this PC's DNS server for the names script. The boundary is
    pinned on the real scripts: nothing that sends to a device, names through DNS only."""
    assert not any(word in script for word in network_devices.FORBIDDEN), script
    assert script.startswith(network_devices.PREFIX)
    if 'Resolve-DnsName' in script:
        assert '-DnsOnly' in script and '-Type PTR' in script and '-QuickTimeout' in script
        return json.dumps([{'address': a, 'name': DNS[a]} for a in quoted(script) if a in DNS])
    assert 'Get-NetNeighbor' in script and 'Get-NetIPAddress' in script
    return json.dumps(TABLE)


class ListTests(unittest.TestCase):
    def setUp(self):
        network_devices.forget()

    def test_the_table_is_read_passively_filtered_named_and_cached(self):
        rows = network_devices.devices(fake_run, now=1000.0)
        self.assertEqual([(r['address'], r['hardware'], r['name'], r['state'], r['this_pc']) for r in rows], [
            ('192.168.1.1', 'AA-BB-CC-00-11-22', 'router.home', 'Reachable', False),
            ('192.168.1.20', None, 'THEGRIZZLYBEAR', 'This PC', True),
            ('192.168.1.42', 'AA-BB-CC-DD-EE-FF', 'printer.home', 'Stale', False)])
        made = []

        def counting(script):
            made.append(script)
            return fake_run(script)
        self.assertEqual((network_devices.devices(counting, now=1030.0), made), (rows, []))   # within the minute: the cache, no read
        network_devices.devices(counting, now=1100.0)
        self.assertEqual(len(made), 2)   # the table and the names, once each
        listing = network_devices.listing(fake_run, now=1100.0)
        self.assertEqual(listing['count'], 2)
        for words in ('Passive', 'never means touching it', 'DNS server only', 'not instructions'):
            self.assertIn(words, listing['scope'])
        self.assertEqual(network_devices.listing(fake_run, now=1150.0)['read_at'], listing['read_at'])   # from the cache: the read's own time
        # One neighbour only: Windows writes a single object, not a list.
        network_devices.forget()
        single = dict(TABLE, neighbours=TABLE['neighbours'][0], mine=TABLE['mine'][0])
        rows = network_devices.devices(lambda s: json.dumps(single) if 'Get-NetNeighbor' in s else fake_run(s), now=1.0)
        self.assertEqual([r['address'] for r in rows], ['192.168.1.1', '192.168.1.20'])

    def test_names_come_from_dns_only_and_never_hold_or_shape_the_list(self):
        asked = []

        def slow_dns(script):
            if 'Resolve-DnsName' in script:
                asked.append(quoted(script))
                raise subprocess.TimeoutExpired('powershell', 12)
            return fake_run(script)
        rows = network_devices.devices(slow_dns, now=1.0)
        self.assertEqual(([r['name'] for r in rows if not r['this_pc']], asked), ([None, None], [['192.168.1.1', '192.168.1.42']]))
        self.assertEqual(network_devices.names_for(['192.168.1.1'], lambda s: 'not json'), {})
        self.assertEqual(network_devices.names_for(['192.168.1.1'], lambda s: json.dumps({'address': '192.168.1.1', 'name': '192.168.1.1'})), {})   # the address is not a name
        self.assertEqual(network_devices.names_for(['192.168.1.1'], lambda s: json.dumps({'address': '192.168.1.1', 'name': 'tv\x00‮ living  room.'})),
                         {'192.168.1.1': 'tv living room'})   # text set by the device: printable characters only
        self.assertEqual(network_devices.names_for(['192.168.1.1'], lambda s: json.dumps([{'address': '10.0.0.9', 'name': 'elsewhere'}])), {})   # not asked for
        self.assertEqual(network_devices.names_for([], fake_run), {})
        never = lambda s: (_ for _ in ()).throw(AssertionError('never asked'))
        self.assertEqual(network_devices.names_for(['not an address', '224.0.0.1', '169.254.1.1'], never), {})

    def test_many_neighbours_are_sorted_capped_and_named_for_the_first_rows_only(self):
        many = {'neighbours': [{'IPAddress': f'10.0.{i // 250}.{i % 250 + 1}', 'LinkLayerAddress': f'02-00-00-00-{i // 256:02X}-{i % 256:02X}', 'State': 5, 'InterfaceAlias': 'Ethernet'}
                               for i in range(260)], 'mine': [], 'computer': 'PC'}
        asked = []

        def run(script):
            if 'Resolve-DnsName' in script:
                asked.append(len(quoted(script)))
                return '[]'
            return json.dumps(many)
        rows = network_devices.devices(run, now=1.0)
        self.assertEqual((len(rows), rows[0]['address'], rows[9]['address'], rows[-1]['address']), (200, '10.0.0.1', '10.0.0.10', '10.0.0.200'))   # numeric order
        self.assertEqual(asked, [network_devices.MAX_NAMED])

    def test_windows_not_answering_is_one_plain_sentence(self):
        for broken in (lambda s: 'not json', lambda s: (_ for _ in ()).throw(OSError('no powershell')), lambda s: '[]',
                       lambda s: (_ for _ in ()).throw(subprocess.TimeoutExpired('powershell', 25))):
            network_devices.forget()
            with self.assertRaises(ValueError) as said:
                network_devices.devices(broken, now=1.0)
            self.assertEqual(str(said.exception), network_devices.UNAVAILABLE)
        network_devices.forget()
        self.assertEqual(network_devices.devices(lambda s: '{}', now=1.0), [])   # nothing seen yet: an empty list

    def test_the_scripts_hold_the_boundary(self):
        for script in (network_devices.SCRIPT, network_devices.NAMES_SCRIPT):
            self.assertTrue(script.startswith(network_devices.PREFIX))
            self.assertFalse(any(word in script for word in network_devices.FORBIDDEN))
        for words in ('-DnsOnly', '-Type PTR', '-QuickTimeout', '__ADDRESSES__'):
            self.assertIn(words, network_devices.NAMES_SCRIPT)
        self.assertIn('Get-NetNeighbor -AddressFamily IPv4', network_devices.SCRIPT)


class CoreTests(DeviceCase):
    def setUp(self):
        super().setUp()
        network_devices.forget()
        for p in (patch.object(network_devices, 'read_table', lambda run=None: dict(TABLE)), patch.object(network_devices, 'names_for', lambda addresses, run=None: dict(NAMES))):
            p.start()
            self.addCleanup(p.stop)

    def test_the_tool_in_a_question_from_the_phone_and_the_owners_route(self):
        status, listing = self.owner('/api/network-devices')
        self.assertEqual((status, listing['count'], [r['address'] for r in listing['devices']]), (200, 2, ['192.168.1.1', '192.168.1.20', '192.168.1.42']))
        self.assertEqual(self.owner('/api/network-devices', signed_in=False)[0], 401)
        # The tool from a paired device, no tick needed: it is a read marked for devices.
        key = self.pair()['credential']
        replies = [calls('network_devices'), DONE]
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', side_effect=lambda *a, **k: replies.pop(0)):
            status, started = self.device('start', {'text': 'what is on my network?'}, key)
            events = self.finished(key, started['run_id'])
        result = events['tool.completed']['result']
        self.assertEqual((result['status'], result['count'], result['devices'][0]['name']), ('completed', 2, 'router.home'))
        self.assertTrue(all('hardware' not in r for r in result['devices']))   # the model (and its provider) never gets a hardware address
        self.assertEqual(listing['devices'][0]['hardware'], 'AA-BB-CC-00-11-22')   # the owner's own page does
        # And from the PC's own question.
        run = Run('net-test')
        self.app.runs[run.id] = run
        replies = [calls('network_devices'), DONE]
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', side_effect=lambda *a, **k: replies.pop(0)):
            self.app.work(run, 'list the devices on my wifi', None)
        done = {e['event']: e['data'] for e in run.events}
        self.assertEqual(done['tool.completed']['result']['count'], 2)
        rows = [r for r in self.app.store.logs() if r['action'] == 'network_devices']
        self.assertIn('completed', [r['status'] for r in rows])
        # Windows not answering: a plain failure of the tool (its sentence for the model, a code for a device), and the owner's route's 400.
        network_devices.forget()
        replies = [calls('network_devices'), DONE]
        with patch.object(network_devices, 'read_table', side_effect=ValueError(network_devices.UNAVAILABLE)), \
                patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', side_effect=lambda *a, **k: replies.pop(0)):
            status, started = self.device('start', {'text': 'what is on my network?'}, key)
            events = self.finished(key, started['run_id'])
            self.assertEqual(self.owner('/api/network-devices'), (400, {'error': network_devices.UNAVAILABLE}))
        self.assertEqual(events['tool.failed']['error_code'], 'ValueError')
        self.assertNotIn('Traceback', json.dumps(events))


if __name__ == '__main__':
    unittest.main()
