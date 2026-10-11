# Security requirements — proposed

Existing desktop stays loopback-only. No public tunnel/Funnel, database port or generic tool endpoint is introduced. Private networking is transport, not authorization.

Before live wearable access: explicit device pairing; hashed revocable device credentials; short-lived scoped sessions; TLS certificate validation; native Keychain storage; no embedded provider/admin secrets. Deny invalid/expired/revoked sessions, replay, cross-device resource access and unknown message fields.

Proposed initial gateway limits: one active turn per device, bounded global queue, 10 turn starts/minute/device, bounded upload bytes and timeout, cancellation and clear BUSY/retry responses. Values are proposed defaults to test, not implemented controls. Rate limits must also cover pairing/auth failures and media traffic.

Start with analysis-only vision and explicitly scoped task/memory operations. Deny desktop source editing, shell, inspection, file export, shutdown and approval APIs. Later sensitive actions require separate server-side authorization and explicit review bound to action arguments and expiry. Captured text cannot authorize a tool.

Logs contain event IDs, durations and safe error codes, not tokens/raw audio/images or private prompts. Test revoked sessions during pending work, reconnect replay, forged device IDs and cancellation of queued speech. Keep mock provider inaccessible in production configuration.
