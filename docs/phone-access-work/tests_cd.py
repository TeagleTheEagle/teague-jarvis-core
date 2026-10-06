

# ---------------------------------------------------------------------------------------------------------------
# Items C and D (docs/PHONE-ACCESS-1.0.17.md sections 2 and 3)

VISION_REPLY = {'choices': [{'finish_reason': 'stop', 'message': {'content': 'A browser with the news, and a terminal.'}}]}


def tiny_jpeg():
    import io
    from PIL import Image
    out = io.BytesIO()
    Image.new('RGB', (8, 8), (20, 40, 60)).save(out, format='JPEG')
    return base64.b64encode(out.getvalue()).decode()


class LocationTests(DeviceCase):
    def test_a_bad_location_is_refused_with_one_sentence(self):
        key = self.pair()['credential']
        for bad in ({'lat': 'x', 'lon': 1}, {'lat': 91, 'lon': 1}, {'lat': 1}, {'lat': 1, 'lon': 1, 'extra': 1},
                    {'lat': 1, 'lon': 1, 'accuracy_m': -1}, {'lat': 1, 'lon': 1, 'label': 'x' * 81}, {'lat': True, 'lon': 1}, 'here'):
            self.assertEqual(self.device('start', {'text': 'Where am I?', 'location': bad}, key), (400, {'error': 'Invalid location.'}), bad)

    def test_the_location_goes_to_that_answer_only_and_is_kept_nowhere(self):
        paired = self.pair()
        key, ident = paired['credential'], paired['device_id']
        bodies = []
        replies = [DONE]
        capture = lambda url, body=None, headers=None, **k: (bodies.append(body), replies.pop(0))[1]
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', side_effect=capture):
            status, started = self.device('start', {'text': 'What is near me?', 'location': {'lat': -33.8688, 'lon': 151.2093, 'accuracy_m': 12, 'label': 'Gumnut Cottage'}}, key)
            self.assertEqual(status, 200, started)
            events = self.finished(key, started['run_id'])
        self.assertIn('assistant.completed', events)
        context = json.loads(bodies[0]['messages'][1]['content'].split(': ', 1)[1])
        self.assertEqual({k: context['device_location'][k] for k in ('lat', 'lon', 'accuracy_m', 'label')}, {'lat': -33.8688, 'lon': 151.2093, 'accuracy_m': 12.0, 'label': 'Gumnut Cottage'})
        self.assertIn('not stored', context['device_location']['note'])
        # Nowhere else: not in the conversation, not in the saved things, not in the activity rows, not in the events.
        everything = json.dumps(self.app.store.history('device-' + ident + '-local')) + json.dumps(self.app.store.items('memory')) + json.dumps(self.app.store.logs()) + json.dumps(list(self.app.runs[started['run_id']].events))
        self.assertNotIn('151.2093', everything)
        self.assertNotIn('Gumnut', everything)
        # A question without a location has no location in its context.
        bodies.clear()
        replies.append(DONE)
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', side_effect=capture):
            status, started = self.device('start', {'text': 'And now?'}, key)
            self.finished(key, started['run_id'])
        self.assertNotIn('device_location', bodies[0]['messages'][1]['content'])

    def test_directions_from_here_start_at_the_devices_position(self):
        import maps
        payloads = []

        def routes(url, payload=None, headers=None, **kwargs):
            payloads.append(payload)
            return {'routes': [{'duration': '600s', 'distanceMeters': 4200, 'polyline': {'encodedPolyline': 'abc'}, 'legs': []}]}
        with patch.dict(os.environ, {'GOOGLE_MAPS_ROUTES_KEY': 'k'}, clear=True), patch.object(maps.providers, 'request', side_effect=routes):
            result = maps.directions('current location', 'Sydney Opera House', 'WALK', location={'lat': -33.8688, 'lon': 151.2093, 'label': 'Gumnut Cottage'})
            self.assertEqual(payloads[0]['origin'], {'location': {'latLng': {'latitude': -33.8688, 'longitude': 151.2093}}})
            self.assertEqual((result['origin'], result['distance_km'], result['mode']), ('Gumnut Cottage', 4.2, 'WALK'))
            self.assertIn('origin=-33.8688%2C151.2093', result['url'])
            # Without a position, "from here" still asks the owner, as before.
            self.assertTrue(maps.directions('here', 'Sydney Opera House', 'WALK')['needs_location'])
            self.assertEqual(len(payloads), 1)


class ScreenTests(DeviceCase):
    def window(self, answer=True):
        """A thread standing in for the PC window: it reads /api/control-requests, uploads one capture and answers."""
        seen, ids = [], set()

        def act():
            for _ in range(200):
                status, listing = self.owner('/api/control-requests')
                self.assertEqual(status, 200, listing)
                for req in listing['requests']:
                    if req['id'] in ids:
                        continue
                    ids.add(req['id'])
                    seen.append(req)
                    if not answer:
                        return
                    status, upload = self.owner('/api/upload', {'name': 'screen-capture.jpg', 'data': tiny_jpeg()})
                    self.assertEqual(status, 200, upload)
                    status, done = self.owner('/api/control-result', {'id': req['id'], 'run_id': req['run_id'], 'result': {'status': 'completed', 'image_submitted': True, 'attachment': upload['id']}})
                    self.assertEqual(status, 200, done)
                    return
                time.sleep(0.05)
        thread = threading.Thread(target=act, daemon=True)
        thread.start()
        return thread, seen

    def test_analyse_my_screen_from_the_phone_is_answered_from_a_capture_the_window_hands_over(self):
        paired = self.pair()
        key, ident = paired['credential'], paired['device_id']
        self.assertEqual(self.owner('/api/control-requests', signed_in=False)[0], 401)
        # Without the tools tick the window's controls are not a device's to ask for.
        replies = [calls('assistant_control', action='analyse_screen'), DONE]
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', side_effect=lambda *a, **k: replies.pop(0)):
            status, started = self.device('start', {'text': 'analyse my screen'}, key)
            events = self.finished(key, started['run_id'])
        self.assertIn('tool.failed', events)
        self.owner('/api/devices', {'action': 'tools', 'id': ident, 'allowed': True})
        thread, seen = self.window()
        replies = [calls('assistant_control', action='analyse_screen'), VISION_REPLY, DONE]
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', side_effect=lambda *a, **k: replies.pop(0)):
            status, started = self.device('start', {'text': 'analyse my screen'}, key)
            self.assertEqual(status, 200, started)
            events = self.finished(key, started['run_id'])
        thread.join(5)
        self.assertEqual([(r['action'], r['run_id'], r['device']) for r in seen], [('analyse_screen', started['run_id'], 'My phone')])
        result = events['tool.completed']['result']
        self.assertEqual((result['status'], result['action'], result['description']), ('completed', 'analyse_screen', 'A browser with the news, and a terminal.'))
        self.assertIn('not kept', result['source'])
        self.assertEqual(self.app.attachments, {})  # the capture is taken by the Core and kept nowhere
        self.assertIn('assistant.completed', events)
        self.assertEqual(self.owner('/api/control-requests')[1], {'requests': []})

    def test_with_no_window_open_the_phone_is_told_plainly(self):
        paired = self.pair()
        key, ident = paired['credential'], paired['device_id']
        self.owner('/api/devices', {'action': 'tools', 'id': ident, 'allowed': True})
        replies = [calls('assistant_control', action='analyse_screen'), DONE]
        with patch.object(assistant_capabilities.Controls, 'DEVICE_TIMEOUT', 0.3), patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', side_effect=lambda *a, **k: replies.pop(0)):
            status, started = self.device('start', {'text': 'analyse my screen'}, key)
            events = self.finished(key, started['run_id'])
        result = events['tool.completed']['result']
        self.assertEqual((result['status'], result['error']), ('unavailable', "The PC's window is not open, so this cannot be done from here."))
        # The window answering without a capture: failed, nothing described.
        thread, seen = self.window(answer=False)
        replies = [calls('assistant_control', action='analyse_screen'), DONE]
        with patch.object(assistant_capabilities.Controls, 'DEVICE_TIMEOUT', 5.0), patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', side_effect=lambda *a, **k: replies.pop(0)):
            status, started = self.device('start', {'text': 'analyse my screen'}, key)
            run_id = started['run_id']
            thread.join(5)
            self.assertEqual(self.owner('/api/control-result', {'id': seen[0]['id'], 'run_id': run_id, 'result': {'status': 'completed', 'image_submitted': False}})[0], 200)
            events = self.finished(key, run_id)
        self.assertEqual(events['tool.completed']['result']['status'], 'failed')
