"""Google routing. Location requests are transient and are not stored here."""
import os
import re
import time
import urllib.parse
import providers


def configuration():
    return {'routes_configured': bool(os.getenv('GOOGLE_MAPS_ROUTES_KEY')),
            'embed_key': os.getenv('GOOGLE_MAPS_EMBED_KEY', '')}


def waypoint(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 300:
        raise ValueError('Enter a starting point and destination (up to 300 characters each).')
    value = value.strip()
    match = re.fullmatch(r'(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)', value)
    if match:
        lat, lng = map(float, match.groups())
        if not -90 <= lat <= 90 or not -180 <= lng <= 180:
            raise ValueError('Invalid location coordinates.')
        return {'location': {'latLng': {'latitude': lat, 'longitude': lng}}}
    return {'address': value}


def directions(origin, destination, mode='DRIVE', location=None):
    """location (1.0.17, docs/PHONE-ACCESS-1.0.17.md item D): the position a paired device sent with its question
    ({'lat', 'lon', 'label'?}); it is the starting point when the owner says "from here". Used for this route only."""
    start, end = waypoint(origin), waypoint(destination)
    if mode not in ('DRIVE', 'WALK', 'BICYCLE'):
        raise ValueError('Choose driving, walking, or cycling.')
    here = origin.strip().lower() in ('current location', 'my location', 'here')
    map_origin = origin
    if here and location:
        start = waypoint(f"{float(location['lat'])},{float(location['lon'])}")
        map_origin = f"{float(location['lat'])},{float(location['lon'])}"
        origin = str(location.get('label') or '').strip() or 'your location'
    elif here:
        return {'needs_location': True, 'destination': destination, 'mode': mode,
                'message': 'Open Maps and choose Use my location or enter a starting address, then calculate the route. Location has not been accessed and no route is calculated yet.'}
    key = os.getenv('GOOGLE_MAPS_ROUTES_KEY', '')
    if not key:
        raise ValueError('Google Routes is awaiting a key. Add GOOGLE_MAPS_ROUTES_KEY locally and enable the Routes API in Google Cloud.')
    payload = {'origin': start, 'destination': end, 'travelMode': mode, 'units': 'METRIC', 'languageCode': 'en-AU'}
    if mode == 'DRIVE':
        payload['routingPreference'] = 'TRAFFIC_AWARE'
    try:
        data = providers.request('https://routes.googleapis.com/directions/v2:computeRoutes', payload,
            headers={'X-Goog-Api-Key': key, 'X-Goog-FieldMask': 'routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline,routes.legs.steps.navigationInstruction.instructions'}, timeout=25)
    except providers.ProviderError:
        raise ValueError('Google Routes request failed. Check the Routes key, enabled API, billing, quota, and network connection.') from None
    routes = data.get('routes', [])
    if not routes:
        raise ValueError('Google found no route. Try more specific addresses or a different travel mode.')
    route = routes[0]
    duration = float(route['duration'].removesuffix('s'))
    return {'origin': origin, 'destination': destination, 'mode': mode, 'duration_seconds': duration,
            'distance_km': round(route['distanceMeters'] / 1000, 1), 'traffic_aware': mode == 'DRIVE',
            'checked_at': time.time(), 'provider': 'Google Maps',
            'polyline': route.get('polyline', {}).get('encodedPolyline', ''),
            'steps': [step['navigationInstruction']['instructions'] for leg in route.get('legs', []) for step in leg.get('steps', []) if step.get('navigationInstruction', {}).get('instructions')],
            'url': 'https://www.google.com/maps/dir/?' + urllib.parse.urlencode({'api': 1, 'origin': map_origin, 'destination': destination, 'travelmode': {'DRIVE': 'driving', 'WALK': 'walking', 'BICYCLE': 'bicycling'}[mode]})}
