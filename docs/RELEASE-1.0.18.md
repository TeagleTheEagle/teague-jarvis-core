# Release 1.0.18: the time fix

Status: **committed on branch `claude/release-1.0.18` (on top of the installed 1.0.17-0d38218c4e1d); the build, the
checks on this PC and the owner's Stage 7 approval follow.** Records of the build and its checks:
`docs/release-rehearsal-20261010-1018-time/README.md` on `claude/main`.

## What the owner asked for

- The Mac's round 6 (`phone/ios/mac/20261010-2005`, STATUS.md "Requests for the PC", item 8): Siri read the Core's
  answer to "what time is it" aloud as raw clock text.
- The owner, 2026-10-10 evening: "keep friday as he is, 1.0.18 time fix only". So 1.0.18 is this one fix on top of
  1.0.17 and nothing else. FRIDAY is not part of it. The Workshop, the devices route, the guard, the You page and the
  other Core fixes on `claude/main` wait for 1.0.19.

## Two earlier builds called 1.0.18 (superseded, never offered)

The number 1.0.18 was first used for the Workshop: build 1 `1.0.18-4afd891c38f4` (every check on this PC passed) and
build 2 `1.0.18-fd2b6fa82121` (with the phone's devices route; its release regression did not pass). Neither was
offered or installed anywhere, so the number is reused, as for 1.0.16 and 1.0.17. On `claude/main`, these belong to
the Workshop (now 1.0.19), not to this release:

- `docs/STAGE7-CHECK-1.0.18.md` as written on 2026-10-10 morning (for build 1; marked superseded, then rewritten for
  this build);
- the top entry of `release-notes.json`, "Release 1.0.18: the Workshop" (to be renumbered 1.0.19 when this branch
  is merged back);
- `docs/release-rehearsal-20261010-1018/` and, on D:, `pkg-1.0.18`, `regression-1.0.18*`, `stage7-local-1.0.18`,
  `setup-rehearsal-v2-1.0.18`, `zip-test-1.0.18-4afd891c38f4`.

This build's folders carry `-time` (`pkg-1.0.18-time`, `regression-1.0.18-time`, `stage7-local-1.0.18-time`,
`setup-rehearsal-v2-1.0.18-time`) or its own release id, so nothing of the Workshop builds is reused or overwritten.

## The defect

"what time is it", "time", "date" and "what is the date" (any letter case, with or without a final `?`, `!` or `.`)
are answered by the Core itself, without the AI: `actions.local_command` turns them into the tool `time_now`, and
`App.describe` turned its result into the reply. In 1.0.17 that reply was `'Local time: ' + result['time']`, the raw
ISO clock reading, for example `Local time: 2026-10-10T14:36:17.893246+11:00`. The PC window showed it as text and Siri
read it out as it was. The same reply went to every device, because the local command runs before the device's own
handling.

## The fix

- `server.spoken_time(stamp)` (new, before `class App`): the reading as one sentence, `It's 2:36 PM on Saturday
  10 October 2026.`: hours 1 to 12 with `AM`/`PM` (`12:05 AM` just after midnight, `12:00 PM` at noon), minutes with two
  digits, seconds left out, the weekday, the day without a leading zero, the month's name and the year. `AM` and `PM`
  are in capitals, as iOS writes a time, so a voice says the letters rather than the word "am". Day and month names
  come from fixed English lists (`DAY_NAMES`, `MONTH_NAMES`), not from the PC's locale, so the sentence is the same
  whatever Windows' language settings are.
- `App.describe('time_now', result)` returns `spoken_time(result.get('time'))`.
- A reading that cannot be parsed (never seen: `time_now` always writes `datetime.now().astimezone().isoformat()`) is
  said as before, `Local time: <reading>`, rather than failing the question.
- Unchanged: the tool `time_now` itself and what it returns (`{'time': <ISO reading>}`), so the AI, when it calls the
  tool in a longer question, still gets the exact reading with its UTC offset (its tool results are the JSON of the
  result, never `describe`); which words reach the local command; the permissions row "Read the time"; the phone's and
  Siri's routes.

## Known limitation (as in 1.0.17)

The sentence is the PC's local time and does not name the time zone. The old reply at least carried the offset
(`+11:00`). A phone away from home in another zone hears the PC's time with nothing to show it; the phone's location
reaches only questions the AI answers, and this one is answered before that. A candidate for 1.0.19, not this release.

## Tests

`test_time_reply.py` (new, 6 tests):

- the sentence for eight readings (the one Siri read out, just after midnight, noon, seconds left out, the last minute
  of the year, a one-digit hour and day, a reading without an offset, a reading in UTC), each also matching the
  general pattern;
- every weekday (Monday 5 to Sunday 11 October 2026) and every month by its English name, from lists written in the
  test itself;
- an unreadable reading is said as it is (`garbage`, `None`, empty);
- `App.describe('time_now', ...)` gives the sentence, and the six phrasings reach `('time_now', {})`;
- a real local Core (`test_device_gateway.DeviceCase`) answering by itself: "what time is it" and "date" through the
  PC's `/api/chat`, and "What time is it?" from a paired phone through `/api/device/start` (the route the iPhone app
  and Siri use). Each run completes with the sentence, no `Local time`, and the tool `time_now` ran. The provider keys
  are taken out of the environment for the test and any call to the AI fails it; the Ollama shadow is off, so the test
  sends nothing to a real local Ollama.

## Independent review (2026-10-10, one reviewer agent)

No high finding; 1 medium and 6 low, all applied:

- **M1** (records): two earlier builds were called 1.0.18 and `claude/main`'s `STAGE7-CHECK-1.0.18.md` still offered the
  Workshop build for approval. The section "Two earlier builds called 1.0.18" above; `claude/main`'s plan marked
  superseded and rewritten for this build; this build's folders carry `-time`.
- **L1** "am"/"pm" may be read as a word by a voice: `AM`/`PM` in capitals. The PC's own voice saying the sentence has
  not been heard (listed under "Not tested" in the release notes).
- **L2** the time zone is no longer shown: the "Known limitation" above.
- **L3** the Core test sent the question to a real local Ollama (the shadow observer, on by default): turned off in
  the test.
- **L4** the test cleared the whole environment and did not prove the AI was never asked: only the two provider keys
  are taken out, and `providers.chat` and `providers.request` fail the test if called.
- **L5** weekdays and the phone's route were not covered, and the test's `finished` overrode `DeviceCase.finished`
  with another signature: every weekday mapped, a paired-phone test added, the PC's helper renamed `pc_events`.
- **L6** wording: the release notes said "the phone and Siri read it out" (the evidence shows Siri), the validation
  cited a README not yet written and suites "at the release commit" that had run on the uncommitted tree, this record
  said "built" before any build and "nothing is stored" though replies stay in the conversation history. Corrected
  here and in the release notes; the suites run again at the release commit.

Checked by the reviewer and found right: the clock edges, odd inputs, locale independence, the weekday and month
mapping; `describe` used only on the local-command path; no other code, test or client (the window, the phone routes,
the action guard, the Ollama shadow, the Mac app) produces or relies on the old text; `server.py` CRLF throughout;
`release-notes.json` valid with every older entry byte-identical.

## Rollback

A rollback to 1.0.17 brings the old reply back (`Local time: <ISO reading>`). This release adds no setting, table or
data format; replies already given stay in the conversation history as they were said. The data, keys and preferences
are untouched by this release in either direction.
