# Whole-interface inspection update

The previous client shortcut accepted only exact phrases and the model's tool schema rejected `all`. The installed tool now supports `panel: all`, and direct phrases including “inspect the whole interface and suggest improvements” start locally without a conversational model round trip.

One in-memory job uses the shared navigation registry in `panel_registry.py`, captures each workspace sequentially in the existing isolated renderer, submits actual image tiles to the configured vision provider when enabled, and consolidates successful panel findings. The existing single-panel endpoint remains supported. Screen Vision is a capture dialog, not a workspace, and is excluded.

Changed components: shared registry; inspection contract, runtime and job coordinator; server inspection route; frontend inspection client and tool-result handler. Conversation diagnostics now record time to first AI text and completed AI response; transcription and speech generation retain their existing separate timings. No faster model or provider has been selected, and no overall speedup is claimed.

Capture defaults to bounded full-panel sections with 80-pixel overlap and at most six tiles per panel. Truncation is explicitly marked. Lazy-loading beyond the isolated fixture, external embeds and virtualized content are not guaranteed. Private record text, drafts, settings values and external data remain withheld. This changes wrapping, so inspection cannot prove the exact typography of private content or functional accessibility.

Jobs have a 15-minute budget checked between operations. Cancellation signals the provider and prevents subsequent panels, but an in-flight capture/provider request can finish. Completed results survive failures/cancellation. Reports expire five minutes after completion. The existing image cache retains at most 18 images for five minutes, so early thumbnails can expire during a large review; analysis uses the actual bytes before eviction. No automatic code/settings changes occur.

Illustrative result (not a live-model result):

```json
{"id":"example","status":"partial","panels":["command","projects"],"results":[{"requested_panel":"command","status":"analysed","stages":{"screenshot_captured":"completed","analysis_completed":"completed"}},{"requested_panel":"projects","status":"failed","errors":["Panel inspection failed."]}],"review_status":"consolidated","review":"Findings from command only; projects could not be reviewed."}
```

Validation: real isolated Chrome capture of all 13 workspace panels and a long scrollable panel; unchanged fixture database and separate page draft/scroll; masking and no side effects; synthetic model delivery and failure tests; one-job phrase routing, combined report, cancellation and timeout tests; existing conversation/voice diagnostics regressions. Cloud-model review quality and the user's actual microphone-to-audible-response latency still require a live trial.

To load, wait until testing is reported complete, save drafts/close reports, mute the mic and use Restart to update. Rollback must restore the prior inspection client, contract, server handler, tool-result handler and capture loop together; remove the new job/registry imports or restore the original panel list before removing those files. Saved user data is not migrated by this change.
