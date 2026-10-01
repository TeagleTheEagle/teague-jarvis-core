# Google Maps setup

## JARVIS custom map

The Maps section now includes a large map, dark JARVIS styling, cyan route lines, start/end markers, a traffic-layer toggle, journey swapping, and travel-time, distance and estimated-arrival cards. Google supplies the geographic data.

For the custom style, enable **Maps JavaScript API** and **Geocoding API** in the existing Google Cloud project. Add both to the API restrictions of the existing **browser/Embed key**, keeping **Maps Embed API** selected. Keep its localhost website restriction. No new key is required and the Routes server key remains separate.

Choose **JARVIS dark** in Map style to retry after updating access. If custom-map access fails, JARVIS shows the standard embedded map and an explanation. The custom route line uses the exact geometry returned with the traffic estimate; the standard embedded map can calculate a different route. Arrival time uses the browser's local timezone. The traffic overlay does not automatically recalculate the estimate.

Reference: https://developers.google.com/maps/documentation/javascript/load-maps-js-api
Address lookup: https://developers.google.com/maps/documentation/javascript/geocoding

Open the Google Cloud console: https://console.cloud.google.com/google/maps-apis/overview

1. Select or create a project and enable billing.
2. Enable **Routes API** and **Maps Embed API**.
3. Create two keys under Credentials:
   - Server key: restrict its API access to **Routes API**. Use an IP application restriction if your outbound public IP is stable. This key stays on the JARVIS server.
   - Browser key: restrict its API access to **Maps Embed API** and its website referrers to `http://127.0.0.1:8765/*` (add `http://localhost:8765/*` only if you use that address). This key is visible to the browser by design; do not reuse the server key.
4. In the `.env` file beside `server.py`, add:

```ini
GOOGLE_MAPS_ROUTES_KEY=your_server_key
GOOGLE_MAPS_EMBED_KEY=your_browser_key
```

5. Restart JARVIS and refresh the browser. Open **MAPS**.

Use **USE MY LOCATION** and allow the browser location prompt, or enter a starting address. Enter a specific destination including its city, then click **CALCULATE ROUTE**. Driving estimates use traffic at request time; walking and cycling do not use traffic. Estimates do not refresh automatically. The embedded Google directions map calculates independently and can differ from the route estimate; use the listed steps for the computed route and Google Maps for live navigation.

Location is requested once when clicked, not continuously tracked. The Maps form keeps it only in page memory. **CLEAR LOCATION** removes the starting location and map; reload also clears the form. Routes send start and destination to Google. When you supply addresses in chat, normal chat storage and the configured AI provider apply. An AI request using “current location” opens Maps and asks you to select the location there; it does not silently obtain GPS.

Configure Google Cloud API quotas and billing alerts for your budget. No Google API calls run until you request a map or route.

References:
- https://developers.google.com/maps/documentation/routes/compute_route_directions
- https://developers.google.com/maps/documentation/embed/embedding-map
- https://developers.google.com/maps/api-security-best-practices
