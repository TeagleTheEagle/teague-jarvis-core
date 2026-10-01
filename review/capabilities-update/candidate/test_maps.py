import os
import unittest
from unittest.mock import patch
import maps


class MapsTests(unittest.TestCase):
    def test_coordinates_and_invalid_inputs(self):
        self.assertEqual(maps.waypoint('-33.8,151.2')['location']['latLng']['latitude'], -33.8)
        for value in ('91,151', '', None):
            with self.assertRaises(ValueError): maps.waypoint(value)

    @patch.dict(os.environ, {'GOOGLE_MAPS_ROUTES_KEY': 'test-only'})
    @patch('maps.providers.request')
    def test_traffic_and_walking(self, request):
        request.return_value = {'routes': [{'duration': '123.5s', 'distanceMeters': 1400, 'polyline': {'encodedPolyline': '_p~iF~ps|U_ulLnnqC_mqNvxq`@'}}]}
        result = maps.directions('Sydney, NSW', 'Mascot, NSW')
        self.assertEqual(result['duration_seconds'], 123.5)
        self.assertEqual(result['polyline'], '_p~iF~ps|U_ulLnnqC_mqNvxq`@')
        self.assertIn('routes.polyline.encodedPolyline', request.call_args.kwargs['headers']['X-Goog-FieldMask'])
        self.assertEqual(request.call_args.args[1]['routingPreference'], 'TRAFFIC_AWARE')
        self.assertNotIn('test-only', str(result))
        maps.directions('Sydney', 'Mascot', 'WALK')
        self.assertNotIn('routingPreference', request.call_args.args[1])

    @patch('maps.providers.request')
    def test_current_location_requires_user_action(self, request):
        self.assertTrue(maps.directions('current location', 'Sydney Airport')['needs_location'])
        request.assert_not_called()

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_key(self):
        with self.assertRaisesRegex(ValueError, 'awaiting a key'):
            maps.directions('Sydney', 'Mascot')

    @patch.dict(os.environ, {'GOOGLE_MAPS_ROUTES_KEY': 'test-only'})
    @patch('maps.providers.request', return_value={'routes': []})
    def test_no_route(self, request):
        with self.assertRaisesRegex(ValueError, 'no route'):
            maps.directions('Sydney', 'London', 'WALK')
