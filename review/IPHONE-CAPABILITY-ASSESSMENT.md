# JARVIS iPhone capability assessment

Assessed 9 September 2026. Device: iPhone 15. User reports iOS 26.6.1; not independently inspected. User has a Windows PC and no Mac. Australian context assumed from this session; account/region eligibility is not verified. This is documentation research and a source inspection, not an iPhone test.

## Decision

Update: User reports being an Apple developer and asks about a native app. Prioritise a native iOS companion with App Intents for the long-term phone interface; Shortcuts remains an optional early connection test. Whether the account has paid Apple Developer Program membership has not been verified. A developer account does not provide a Mac or bypass iOS sandbox/background restrictions. No native app has been built or installed. Backup cfb5b1d5fb60437ab180485f0d95f200 was created and verified, and its restore rehearsal passed before connection implementation. No phone bridge has yet been implemented.

Pursue a system-integrated assistant experience using supported iOS entry points, initially Shortcuts connected to the existing Windows-hosted JARVIS service. Do not describe this as replacing iOS, installing a new phone OS, or gaining unrestricted device control. Native App Intents/extensions are a later option requiring a compatible macOS build/signing environment.

OpenAI quota exhaustion does not block local development, secure transport, pairing, database operations, deterministic commands, or simulated API-failure tests. It does block validation of actual OpenAI conversation, reasoning and vision. Existing speech synthesis has separate provider availability/billing; do not assume it is unavailable or free. Siri/dictation can have their own connectivity requirements.

## Capability matrix

| Desired experience | Assessment and implementation boundary | Proof required |
| --- | --- | --- |
| Replace iOS or its Home Screen system | No supported route established on this iPhone. Apple verifies a signed boot chain. An app cannot become the kernel or remove sandbox restrictions. | Not a proposed milestone. |
| Invoke JARVIS by voice | Siri can run a named Shortcut, which can request JARVIS. This still uses Siri as the entry point, not a custom system wake word. | Run a named shortcut, including locked/unlocked behaviour. |
| Quick physical access | Back Tap can run a Shortcut. Do not assume an Action button on a standard iPhone 15. | Test gesture reliability and required unlocks on this phone. |
| Tasks, memories and projects shared with desktop | Feasible design using local backend data and authenticated requests. Not implemented on the phone. | Create a uniquely labelled test task, verify desktop readback, remove test data. |
| Calendar/reminders | Apple exposes permission-controlled access via EventKit for native apps. Investigate the specific built-in Shortcuts actions available on this phone for the first prototype. | Create and read back a test reminder; exercise denied permission. |
| Send a message | Standard native message composer presents a user-operated send interface. Shortcuts may provide additional explicit workflows. Do not infer arbitrary silent sending or message-history access. | Inspect selected route and test with user-selected recipient/content only. |
| Calls | Opening a supported calling workflow is distinct from answering cellular calls or accessing call audio. Default-app categories do not grant unrestricted telephony. Region/entitlement support must be checked before committing. | Dedicated assessment before implementation. |
| Open/control other apps | Only actions exposed by Shortcuts, app integrations or supported links. No universal mouse/keyboard-style controller for other iPhone apps established. | Verify each app and action separately. |
| Notifications from every app | Do not promise global access. Apple now documents Accessory Notifications; exact accessory, entitlement, OS and region eligibility remains unresolved. That is not proof of a general JARVIS notification reader. | Check official eligibility and actual phone settings before designing around it. |
| Photos/camera | Start with intentional sharing/capture. Camera capture, visual understanding and background capture are separate capabilities. No always-on camera promise. | Share a test image; test analysis once model access works. |
| Always listening while locked | Not an established supported capability for this assistant. Background execution is purpose-specific, not an unrestricted permanent process. An active audio session is not proof of a reliable system wake-word replacement. | Battery, lock-screen, interruption and termination testing if a supported route is identified. |
| TV, cameras and glasses | Separate integrations, not obtained automatically by connecting the iPhone. | Inventory exact devices, documented APIs and account permissions first. |

## Existing code constraint

server.py binds to 127.0.0.1 and checks loopback Host/Origin. Keep those desktop protections. Do not simply bind the full desktop server to all network interfaces or expose desktop execution endpoints to the phone.

Proposed bridge: encrypted connection, revocable device credential, narrowly allowed task/memory operations, bounded inputs, explicit operation results and idempotency for retried writes. Provider credentials stay on the PC. The PC must be awake/reachable. Remote access is a later milestone.

## First build milestone without paid model calls

1. Verify a backup and map existing task APIs.
2. Implement a narrow authenticated bridge with encrypted transport; decide certificate/private-network setup before deployment.
3. Test unauthenticated access, revoked credentials, invalid input, repeated requests and backend unavailability locally.
4. Construct a Shortcut on the iPhone that submits a task title and displays the real saved result.
5. Optionally invoke that Shortcut through Siri or Back Tap. Use typed input first so speech recognition does not obscure connection failures.
6. Verify the same task appears on desktop. Record actual result and timestamp.

This milestone validates a phone-triggered JARVIS action without pretending to validate free-form intelligence. A later native client could expose richer system actions through App Intents. Access to a Mac or legitimate hosted Mac build environment is needed for that build/test/signing stage; purchasing hardware is not required for the first Shortcuts prototype.

## Official sources

- [Apple secure boot](https://support.apple.com/guide/security/boot-process-for-iphone-and-ipad-devices-secb3000f149/web): signed boot chain.
- [iOS runtime security](https://support.apple.com/guide/security/security-of-runtime-process-sec15bfe098e/web): sandbox and explicit services.
- [Siri invokes Shortcuts](https://support.apple.com/en-ie/guide/shortcuts/apd07c25bb38/ios).
- [Shortcuts web requests](https://support.apple.com/guide/shortcuts/request-your-first-api-apd58d46713f/9.0/ios/26).
- [Back Tap](https://support.apple.com/en-au/111772).
- [App Intents](https://developer.apple.com/documentation/appintents).
- [Background strategies](https://developer.apple.com/documentation/backgroundtasks/choosing-background-strategies-for-your-app).
- [EventKit](https://developer.apple.com/documentation/eventkit/creating-events-and-reminders).
- [Message composer](https://developer.apple.com/documentation/messageui/mfmessagecomposeviewcontroller).
- [Default apps](https://support.apple.com/en-au/121430).
- [Accessory Notifications](https://developer.apple.com/documentation/accessorynotifications): eligibility needs further verification; not claimed available to this project.
- [Xcode requirements](https://developer.apple.com/xcode/system-requirements).

Some Apple Developer pages rendered only a JavaScript shell; official search excerpts support the limited descriptions above. Do not treat undocumented details as established. No runtime changes, firewall changes, live phone tests, API calls or purchases were made in this assessment.
