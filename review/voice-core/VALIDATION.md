# Holographic voice core validation

Shared renderer: static/voice-core.js. Main/compact/picture-in-picture use the existing movable core canvas. The desktop companion imports the same renderer and receives bounded samples, bands and input level over the existing IPC channel.

Audio: existing MediaElementAudioSource/Analyser path retained; FFT expanded to 2048 samples. RMS, low/mid/high band data and time-domain samples come from playing audio only. Speech energy rises trigger outward pulses. Incoming measured microphone level triggers inward pulses. The renderer uses exponential attack/release smoothing, smoothed waveform points and trailing samples. No sampled waveform is fabricated when browser speech synthesis cannot expose audio.

Validation performed: 105 Python tests, 13 desktop Node tests, all 13 pages rendered in isolated browser with zero JavaScript errors, companion fixture test. Real Web Audio oscillator at two amplitudes plus silence drives the renderer; results.json records measured response. Output was muted. Screenshots include test-tone samples, not a recording of JARVIS. Native provider speech, subjective audibility, hardware frame rate and live interruption remain unverified.

The updater must load the source changes before the running desktop uses this renderer. No voice provider or saved setting was changed. No user audio was saved or uploaded by these checks.
