# Local voice prototype

Open Settings → Open local voice lab, or http://127.0.0.1:8765/voice-lab.html.

## Test with your SteelSeries headset

1. Mute JARVIS in other tabs. Enable the microphone in the lab and allow browser access. If device names are initially hidden, enable once, mute, then select the SteelSeries microphone or Sonar microphone input and enable again. The actual input name appears below the selector.
2. Hold **Hold to talk**, say “The meeting starts at nine tomorrow morning,” then release. Recognised text should appear without creating any task or sending any command.
3. Say **Hey Jarvis**, wait for the bright listening pulse, then say the same sentence. Pause to finish. Standalone “Jarvis” is not the pretrained model's supported baseline.
4. Repeat 20 times in quiet conditions, then 20 with normal background noise. Mark missed and false activations using the counters. Leave it listening for five minutes without the wake phrase and record false triggers. Counters are session-only; note the results before refreshing.
5. Optionally play a local audio sample through the lab's playback control. The microphone closes during playback and must be manually re-enabled. This does not protect against audio from another application; use the headset and mute other JARVIS tabs.
6. Disconnect the network and repeat transcription after installation. The lab needs no cloud service. The main JARVIS language model still uses its existing provider.
7. With the lab listening, sleep and resume Windows. The lab should detect stopped audio and offer manual re-enable. Unplug/reconnect the headset and check the selected input. Actual device recovery remains to be tested.

No microphone recordings or transcripts are written to disk by this prototype. Audio is processed in memory; transcripts remain on the page until cleared or closed. No automatic cloud fallback exists. Existing assistant tools, approval rules, credentials and startup configuration are unchanged.

## Implementation and boundaries

- `static/voice-lab.html`, `.css`, `.js`: isolated UI, selected microphone capture, level meter, ordered bounded wake queue, push-to-talk, state indicators, manual recovery and local playback isolation. Reuses the existing 16 kHz microphone worklet and local wake endpoint.
- `local_stt.py`: PCM validation, serial CPU int8 Whisper base.en transcription and Silero speech filtering. Model loading uses local files only.
- `setup_local_voice.py`, `requirements-local-voice.txt`: explicit one-time install/download. Not run on application startup or microphone enable.
- `server.py`: authenticated lab status/transcription endpoints and static routes. Lab entry issues the same local session cookie as the home page. Rejected POST connections close so unread audio bytes cannot be parsed as a subsequent request after a restart. Authentication rules are unchanged.
- `static/reliability.js`: Settings link.
- `test_local_stt.py`, `test_voice_lab.cjs`, `check_voice_offline.py`: validation.

The original production voice path is not replaced yet. The lab eliminates deliberate alternate-chunk skipping. It stops visibly if detection falls behind by six queued chunks, instead of silently dropping sound. Utterance ending still uses a provisional energy threshold plus silence timer; trained Silero VAD filters the captured utterance before transcription. Tune against headset measurements before promoting this to production.

## Measured on 8 September 2026

- 62 Python tests passed; Node audio-ordering, overload, cancellation and existing speech-cancellation checks passed.
- Real Whisper load plus one second of silence returned an empty transcript with Python socket connections blocked. First measured cold load: 37.125 seconds.
- Windows synthetic speech (2.98 seconds), held only in memory, transcribed as “The meeting starts at 9 tomorrow morning.” Network socket connections blocked: 1.312 seconds first request, 0.625 seconds repeat. This tests engine operation, not microphone recognition or wake accuracy.
- Desktop browser page visually checked; local model status displayed correctly.
- Not yet measured: SteelSeries wake accuracy, noisy-room false triggers, full wake-to-text latency, real sleep recovery, narrow-screen visual layout, or real headset playback isolation.

## Licensing and next phases

[faster-whisper](https://github.com/SYSTRAN/faster-whisper) and [Whisper](https://github.com/openai/whisper) use MIT licensing. Silero VAD is MIT. Existing [openWakeWord](https://github.com/dscripka/openWakeWord) code is Apache 2.0; its pretrained wake models are CC BY-NC-SA 4.0. Review that noncommercial restriction before redistribution or commercial use.

After live measurements: improve endpointing, integrate validated local transcripts with existing approval handling, then evaluate local TTS separately. A custom voice still requires a speech engine and owned or explicitly consented training recordings. It does not repair microphone routing or missed wake words, and matching the present Fish Audio voice is not promised.

## Main interface integration

The main interface now uses ordered wake audio and the local PCM transcription endpoint. Audio has no automatic cloud transcription fallback; recognised text still goes through the existing assistant and tools. Fish Audio output is unchanged. Settings provides a microphone selector, and Hold to talk bypasses the wake phrase while idle. Detection pauses during assistant replies. Microphone disconnects or stopped audio require manual re-enable. Main input ordering, raw PCM, playback suppression and stale-wake tests passed, along with 69 Python tests. The user reported successful quiet/noisy wake tests and transcription in the lab; main-interface spoken command validation remains for their return.

## Conversation sessions

Hey Jarvis opens a session. Listening resumes after each reply without another wake phrase. Say Thank you Jarvis as a standalone utterance to close the session and return to wake-only listening; it does not mute the microphone. Stop/cancel/silence also ends the session. A 2.56-second pause submits a turn. After 12 seconds without speech, a single Anything else, sir? prompt is spoken, then listening resumes. No repeated prompts until more speech. Playback still pauses capture to prevent self-triggering; use push-to-talk to interrupt. These are timing rules, not inferred awareness. Unit tests cover session retention, bounded silent audio, single nudge, pause tolerance, resume and exact end-phrase matching. Live user validation of the new conversation flow remains outstanding.
