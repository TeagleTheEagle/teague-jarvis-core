# Speech through Qwen as well (release 1.0.15, scope item 5)

Built 2026-10-06 in the repo only, independently reviewed (2 high, 3 medium and 5 low findings, all applied:
section 4). Master document section 4: speech in and speech out through the providers the owner uses, with the
local path kept.

**Before:** the microphone's words were always turned into text on this PC (Whisper). A cloud route existed for
OpenAI only; nothing in the window used it, and it would send any recording it was given. The Qwen cloned voice
needed a voice ID, and there was no way to make or check one.

## 1. One setting: who turns speech into text

Settings > AI > **Speech recognition** (setting `speech_recognition`):

| Choice | What happens |
|---|---|
| **On this PC** (default; what JARVIS did until now) | Whisper on this PC. Nothing the microphone hears leaves the PC until it is text. |
| **In the cloud, by your AI provider** | The recording of each command is sent to the provider chosen in the key file: Qwen (`qwen3-asr-flash`) or OpenAI (`gpt-4o-mini-transcribe`). The line under the choice says which one, or that none is available. |

Rules (`App.transcribe_speech`, route `POST /api/speech-to-text`, `providers.transcribe`):

- **What "the recording of a command" is.** Detecting the wake word always happens on this PC. What is then recorded
  and, with the cloud choice, sent: about a second from before the wake word was recognised (normally "Hey Jarvis"
  itself) and the command up to the pause after it, at most 30 seconds. In an open conversation, with hold to talk,
  and when you interrupt a spoken reply, each thing you say is recorded the same way without a wake word. Nothing
  else the microphone hears is recorded or sent.
- **If the cloud cannot, this PC does it.** A refusal, no connection, an answer that is not text, or no answer within
  8 seconds: the local recognition takes over, and the microphone diagnostics say that this PC did it and why. If
  this PC cannot either (no local model installed), the message gives both reasons. With no key for the chosen
  provider, or while the emergency stop holds, this PC does it and nothing is tried.
- **Never the cloud while the emergency stop holds** (a recording already on its way when the stop is pressed cannot
  be called back; its text is then refused as a question), and never for another device: a paired device's or the
  glasses test client's recording is always turned into text on this PC.
- **The voice lab page is always this PC**, as that page says (`/api/voice-lab/transcribe` is the local
  recognition only).
- Only the provider the owner chose is used; the other provider's key is not touched for this.
- The recording is 16 kHz mono, sent as a WAV file. Nothing is stored and nothing is written to the activity log.
- The older route `POST /api/transcribe`, which sent whatever recording it was given to the cloud whatever the
  setting said, is removed.

**Qwen request, as Alibaba's API reference gives it (read 2026-10-06, through a summary of the page):**
`POST <base>/chat/completions`, model `qwen3-asr-flash`, one user message holding the recording as `input_audio` (a
base64 data address), `asr_options` with `enable_itn` (numbers as digits, as the local recognition writes them) and
`language` `en`. The text comes back in `choices[0].message.content`. Key-file lines that change it: `QWEN_ASR_MODEL`,
`QWEN_ASR_LANGUAGE` (an empty value lets Alibaba detect the language). Alibaba's limit of 10 MB per recording is far
above what JARVIS sends.

**Not measured, and to know before choosing the cloud:** how fast and how accurate Qwen's recognition is next to the
local one on the owner's voice. The local recognition is told the words "Jarvis" and "Mr. Teague" in advance; the
cloud request is not, so the name, "thank you Jarvis" and the stop words may be heard less reliably. That needs the
owner's key and voice to find out; the choice is there to try, and the local default is unchanged. Cost: Alibaba
charges speech recognition by the second of sound (see their price list); a spoken command is a few seconds.

## 2. The Qwen cloned voice: an owner-run tool

`tools/host/Test-QwenVoice.ps1` (run by the owner in PowerShell, jonny account; it reads the key file itself and
never shows a key; Claude never reads key files):

```
powershell -ExecutionPolicy Bypass -File C:\Users\jonny\JARVIS-claude-workspace\repo\tools\host\Test-QwenVoice.ps1
```

- **Without a switch:** lists the cloned voices on the Alibaba account of the key, says which one the key file
  names (`QWEN_TTS_VOICE`), says so when that voice is not on the account or was made for another model, and makes
  one short spoken test with it, saved as a sound file to play. Two or three requests; well under one US cent. An
  answer from Alibaba that is not a list of voices is said to be that, never read as "no voices".
- **`-Enroll <recording>`:** creates a new cloned voice from a recording (10 to 20 seconds of clear speech by one
  speaker; WAV 16-bit, MP3 or M4A; mono; 24 kHz or better; at most 60 seconds and 10 MB). A WAV file is checked
  against those rules before anything is sent. Alibaba charges for creating a voice (a small one-off amount; about
  one US cent on their page of 2026-10-06), so the owner types YES first. It prints the new voice ID and the line
  for the key file (`QWEN_TTS_VOICE=...`).
- **Two keys:** JARVIS prefers a Windows variable named `DASHSCOPE_API_KEY` over the line in the key file, and the
  tool uses the key file. When the two differ the tool says so (without showing either), because the voice would
  then be made on another account than the one JARVIS speaks with. (On 2026-10-05 the owner's two held the same
  value.)

After the key file has the voice ID: quit JARVIS completely, start it again, and choose Settings > Voice > VOICE
PREVIEW > Qwen.

The requests are Alibaba's documented ones (voice list and creation: `.../api/v1/services/audio/tts/customization`,
model `qwen-voice-enrollment`; the spoken test: the same request JARVIS sends). The key is only ever sent to an
`https://*.aliyuncs.com` address, and a redirect answer ends the request: neither the key nor the recording is sent
on to another address.

## 3. Checked

`test_speech_recognition.py` (16 tests: which provider does the cloud recognition; the Qwen request and both answer
shapes; what is refused before sending; anything but text in an answer is an error; one short request and no second
try on the microphone path; a request that carries a key is never sent on by a redirect; in the Core: this PC by
default with nothing sent, the cloud when chosen with an 8-second limit, this PC whatever goes wrong in the cloud,
both reasons when neither can, never the cloud while stopped, a recording that is not one, the setting; the voice lab
route stays local; the window's route; the old cloud route gone). `tools/host/check_qwen_voice_tool.py` runs the voice
tool against a stand-in for Alibaba on this PC with a made-up key: 37 of 37 checks (listing, an answer that is not a
list, more voices than are shown, the spoken test from an answer and from a link, creating a voice, recordings
Alibaba would refuse stopped before sending, two unusual WAV files, a refusal shown without the echoed key, a
redirect, a different Windows variable, addresses that are not Alibaba's refused). In the sandbox window: the choice
is shown under Settings > AI, saved and read back; with no key the cloud is not tried.

**Not checked, and it cannot be from here:** anything against Alibaba or OpenAI themselves (no request was sent to a
provider; the request shapes are from Alibaba's pages, read through a summary, not from a live answer); the
recognition quality question above. The owner's first run of the tool, and the first spoken command with the cloud
choice, are the real test.

## 4. Independent review (one reviewer, 2026-10-06): 2 high, 3 medium and 5 low findings, all applied

The reviewer read this document and the change, ran experiments with the network replaced and a clean environment,
and read Alibaba's pages (through summaries). The fixes were not reviewed again.

**High**

1. The voice lab page would have sent its recordings to the cloud with the cloud choice, while saying "No cloud
   used" (read, confirmed by a run). **Fixed:** the voice lab's route is the local recognition again; the window's
   microphone has its own route.
2. A slow or hung provider blocked voice and typing for 60 seconds (Qwen) or 122 seconds (OpenAI) and then ran the
   stale command; during that time no wake word and no spoken stop was heard (run). **Fixed:** one request of at most
   8 seconds and no second try on the microphone path, then this PC does it.

**Medium**

3. The older route `POST /api/transcribe` sent any recording to Qwen whatever the setting said (run). **Removed.**
4. Several cloud failures did not fall back, so the words were lost (an answer cut off, an answer that was not text;
   run). **Fixed:** whatever goes wrong in the cloud, this PC does it; an answer without text is an error, never
   "nothing was said"; when neither can, both reasons are given.
5. Sentences that said more than the code: "only what is said after the wake word is sent" (the recording includes
   the wake word and about a second before it, and every utterance of an open conversation), "never lost", and
   several texts in the window and in older documents that still said "local" without qualification. **Corrected**
   here, in the window (Settings help, the microphone label, the status while transcribing), in `README.md` and in
   `VOICE-AND-MEMORY.md`.

**Low**

6. The voice tool read an answer it did not understand as "0 voices". **Fixed.**
7. The tool could create the voice on another account than JARVIS uses (a Windows variable against the key file).
   **Fixed:** it says so.
8. A redirect answer made PowerShell send the recording on to the new address; and JARVIS's own provider requests
   sent the key on with a redirect (older than this item). **Fixed in both:** a request that carries a key is ended
   by a redirect (`providers._KeysStayPut`; requests without a key follow redirects as before).
9. WAV files with a sound part whose size was never filled in, or with a part named `DATA`, were misread.
   **Fixed.**
10. `QWEN_ASR_MODEL` and `QWEN_ASR_LANGUAGE` are now in `env.template`; the Settings line no longer blames a missing
    key for an unsupported provider and says what happens while stopped; "two or three requests".

**Checked by the reviewer and found correct:** with the default nothing is sent and the local result is the old one;
both paths refuse the same recordings; other devices and Stage 4 never reach the cloud; only the chosen provider is
used; nothing of a recording is stored or logged; the Qwen request, the voice list and the voice creation match
Alibaba's pages; the tool never printed the key (also when Alibaba echoed it), runs on PowerShell 5.1, and sends
nothing without the typed YES; the Settings choice is saved and restored.

**Not reached by the review:** anything against the providers themselves; the Settings choice in a real window
(done by the author, section 3); recognition quality.
