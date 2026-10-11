# Device-independent contracts — proposed

WearableDevice exposes asynchronous captureAudio, playAudio, captureImage, streamCamera, getDeviceState, getBatteryState, displayText, displayImage, displayStatus and gesture events. Each operation checks capabilities AND current permission; unsupported operations return a typed UNSUPPORTED error, never a successful no-op. Battery may be null. Streaming uses cancellable bounded queues, not an unbounded frame feed.

States: OFFLINE, IDLE, LISTENING, THINKING, LOOKING, SPEAKING, EXECUTING, ERROR. Separate camera states: OFF, READY, CAPTURING, ANALYSING, ERROR. READY means permitted and available, not recording. Reconnect returns IDLE; never resumes capture automatically.

Adapters: MockWearableAdapter first; MetaWearableAdapter on native iPhone later. AndroidXRAdapter and TeagueGlassesAdapter are future names, not claimed implementations. Native iPhone capture can implement the same contract without owning glasses.

Protocol envelope: version, request_id, turn_id, operation and bounded payload. Authenticated identity is assigned by server, not trusted from JSON. Explicit image MIME/size/dimensions and PCM sample rate/channel count; reject arbitrary file paths, malformed base64 and incompatible formats. Correlate responses and cancel late playback after interruption/disconnection.

Timing: client monotonic speech end, upload start/end and playback start; server monotonic STT start/end, context load, provider request, first token if truly streamed, vision completion, TTS start and first audio. Link via turn ID; never subtract monotonic clocks on separate machines. Measure round-trip network timing separately, mark unavailable stages null. Fake timings are labelled simulated and excluded from live comparisons.

Milestone 3 mocks fixture PCM, image frames, connection, battery, permissions, output audio and future display. Speaker fixture playback/sink checks do not prove live TTS voice quality. Simulated scene answers must visibly say DEVELOPMENT MOCK; they are not actual vision inference.
