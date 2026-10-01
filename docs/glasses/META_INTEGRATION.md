# Meta capability assessment

Checked 9 September 2026 against public official sources. No physical device or SDK build tested. Detailed developer documentation returned a login requirement; exact app configuration and hardware eligibility remain to verify after developer access. Search snippets are not sufficient to implement SDK calls.

| Capability | Assessment | Consequence |
|---|---|---|
| Ray-Ban Meta Gen 1/2, Display, Oakley HSTN/Vanguard | SUPPORTED in published portfolio list [1] | Verify exact glasses model, firmware and market before purchase. |
| Camera photos/video stream | SUPPORTED [2][3] | Use deliberate capture; initial request uploads one frame. |
| Microphone/speakers | PARTIALLY SUPPORTED for our design: official Bluetooth profile route [1] | Native OS audio session and actual route readiness must be tested; not a guaranteed DAT audio stream. |
| Display/HUD | SUPPORTED on Display hardware [3][4] | Capability-gated; ordinary displayless glasses cannot render HUD. Defer implementation. |
| Mock camera/media/permissions/device states | SUPPORTED [5] | Use official Mock Device Kit during native integration, alongside our Windows mock. |
| Mock display | NOT SUPPORTED per current FAQ [1] | A custom future-HUD mock is not proof of Meta display compatibility. |
| Phone and pairing | SUPPORTED via iOS/Android; Meta AI app pairs glasses [1] | iPhone client is a necessary part of this prototype. |
| SDK packaging | SUPPORTED via Swift Package Manager [2] | Pin a tested version; do not copy old sample APIs. |
| iOS requirement | SDK 0.9.0 minimum 17.2 [3] | Reported iOS 26.6.1 exceeds minimum; exact Xcode/device compatibility untested. |
| Bluetooth / Wi-Fi | SDK 0.8 added Wi-Fi transport; 0.9 mock checks required link configuration [3] | Exact networking/permissions must follow chosen release docs; do not assume Bluetooth-only media. |
| Registration and permissions | SUPPORTED lifecycle, permission simulation [2][5] | Developer Mode and real user consent required. Exact registration identifiers/redirects remain UNKNOWN until detailed setup is verified. |
| Background/locked phone | PARTIALLY SUPPORTED, feature-specific [3] | 0.9 sample distinguishes recording from preview background behavior. Continuous conversational operation needs physical testing. |
| Custom JARVIS wake word/system assistant replacement | UNKNOWN / not established by consulted current sources | Do not promise takeover of Meta wake word, iOS side button or permanent listening. |
| Battery percent, gesture coverage, route latency | UNKNOWN / NEEDS TESTING for selected device/API | Report unavailable until measured/verified. Do not fabricate telemetry. |
| Public distribution | NOT SUPPORTED during current developer preview [1] | Prototype/test-release work only; membership does not override Meta restrictions. |

Latest public changelog inspected: 0.9.0 (3 August 2026). Its camera lifecycle differs from older tutorials. Public sources establish feasibility, not guaranteed performance or access for this user's account.

## Official sources

1. [Meta FAQ](https://developers.meta.com/wearables/faq/) — hardware, pairing, audio, mock-display limitation and distribution.
2. [Official iOS SDK repository](https://github.com/facebook/meta-wearables-dat-ios) — package setup, registration overview, analytics and crash-reporting opt-outs.
3. [Official iOS changelog](https://raw.githubusercontent.com/facebook/meta-wearables-dat-ios/main/CHANGELOG.md) — version-specific lifecycle, minimum OS and transport changes.
4. [Meta display announcement](https://developers.meta.com/blog/build-for-display-glasses/) — display development route.
5. [Mock Device Kit](https://wearables.developer.meta.com/docs/mock-device-kit/) — camera/media/permission simulation; public indexed material available, full page access restricted here.

No firmware modification, jailbreak, security bypass, new account signup or hardware purchase performed.
