# Capture and retention — proposed

No wearable recording or transmission added by this audit.

Intended flow: deliberate capture on glasses -> paired iPhone -> encrypted gateway on PC. Local STT retains audio in memory. If cloud STT is explicitly selected, audio leaves the PC for that provider. Vision sends the selected frame and relevant prompt/context to the configured vision provider. TTS sends response text to the configured voice provider. These are external services even though the database is local.

Mock mode uses chosen fixtures and makes no provider calls. Use non-personal fixtures by default. Camera/mic permissions are independent; denial must leave text/device controls usable. Capture states stay visible on the phone and use supported hardware indicators.

Frames/audio are ephemeral by default and cleared after the turn/cancellation. Existing conversation storage must be disclosed; do not silently claim all turn data is ephemeral. Explicit 'remember this' may retain selected text and an image reference; location requires separate permission. No automatic facial identification, continuous surveillance or indiscriminate frame archive.

Before persistent visual memory: implement retention controls, delete image plus related references, backup-retention disclosure and encryption-at-rest strategy. Existing SQLite/backups are not automatically encrypted by this proposal. Deleting a live memory does not erase earlier backups. Review Meta SDK analytics/crash-reporting opt-out settings during integration.
