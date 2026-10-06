import AVFoundation
import Foundation

/// Hold to speak: records the phone's microphone as 16 kHz mono 16-bit PCM, the Core's format
/// (local_stt.transcribe: 0.1 to 30 seconds), and hands the bytes over when the finger lifts.
/// The audio engine calls back on its own thread; everything shared goes through one lock.
final class AudioRecorder {
    private let engine = AVAudioEngine()
    private let lock = NSLock()
    private var pcm = Data()
    private var running = false   // bytes are being collected
    private var armed = false     // a hold is in progress (from start() until stop())
    private var progress: ((Double) -> Void)?
    private var limitReached: (() -> Void)?
    private var failed: ((String) -> Void)?
    private var configurationObserver: NSObjectProtocol?

    static let sampleRate: Double = 16_000
    static let limitSeconds: Double = 30
    private var limitBytes: Int { Int(AudioRecorder.sampleRate * AudioRecorder.limitSeconds) * 2 }

    /// The audio session both the recorder and the player use: the phone's own microphone and speaker, or a
    /// Bluetooth headset when one is connected. With both options set, iOS keeps a headset that has both profiles on
    /// HFP (its microphone works; its sound is at call quality while it is connected); a headset with A2DP only
    /// plays the reply in stereo and the phone's own microphone records. `allowBluetoothHFP` is the iOS 26 SDK's
    /// name (available from iOS 26, this project's minimum); `allowBluetooth` is the same option's older name,
    /// kept for an older Xcode.
    static var sessionOptions: AVAudioSession.CategoryOptions {
        #if compiler(>=6.2)
        return [.defaultToSpeaker, .allowBluetoothHFP, .allowBluetoothA2DP]
        #else
        return [.defaultToSpeaker, .allowBluetooth, .allowBluetoothA2DP]
        #endif
    }

    init() {
        // A headset connecting or disconnecting mid-hold stops the engine on its own (the input format changes);
        // the hold ends there and the owner is told, instead of a silent recording. On the main queue, where
        // stop() also talks to the engine: the engine is not thread-safe.
        configurationObserver = NotificationCenter.default.addObserver(forName: .AVAudioEngineConfigurationChange, object: engine, queue: .main) { [weak self] _ in
            self?.routeChanged()
        }
    }

    deinit {
        if let configurationObserver { NotificationCenter.default.removeObserver(configurationObserver) }
    }

    /// Ask the system's microphone question early (when the Ask screen first shows), not in the middle of a hold.
    static func requestPermissionEarly() {
        AVAudioApplication.requestRecordPermission { _ in }
    }

    func start(progress: @escaping (Double) -> Void, limitReached: @escaping () -> Void, failed: @escaping (String) -> Void) {
        lock.lock()
        armed = true
        running = false
        pcm = Data()
        lock.unlock()
        self.progress = progress
        self.limitReached = limitReached
        self.failed = failed
        AVAudioApplication.requestRecordPermission { [weak self] granted in
            guard let self else { return }
            guard self.isArmed else { return }   // the finger lifted before the answer came: nothing to record
            guard granted else {
                failed("The microphone is not allowed for JARVIS on this phone. Allow it in the iPhone's Settings > Privacy & Security > Microphone.")
                return
            }
            self.begin()
        }
    }

    private var isArmed: Bool {
        lock.lock()
        defer { lock.unlock() }
        return armed
    }

    private func begin() {
        guard isArmed else { return }
        do {
            let session = AVAudioSession.sharedInstance()
            try session.setCategory(.playAndRecord, mode: .default, options: AudioRecorder.sessionOptions)
            try session.setActive(true)
            let input = engine.inputNode
            input.removeTap(onBus: 0)   // never two taps on the bus: a second one ends the app
            let source = input.outputFormat(forBus: 0)
            guard source.sampleRate > 0, source.channelCount > 0 else {
                failed?("No microphone input is available.")
                return
            }
            guard let target = AVAudioFormat(commonFormat: .pcmFormatInt16, sampleRate: AudioRecorder.sampleRate, channels: 1, interleaved: true),
                  let converter = AVAudioConverter(from: source, to: target) else {
                failed?("The recording could not be converted to JARVIS's format.")
                return
            }
            lock.lock()
            running = true
            lock.unlock()
            input.installTap(onBus: 0, bufferSize: 4096, format: source) { [weak self] buffer, _ in
                self?.consume(buffer, converter: converter, target: target)
            }
            engine.prepare()
            try engine.start()
        } catch {
            lock.lock()
            running = false
            lock.unlock()
            failed?("The microphone could not be started.")
        }
    }

    private func consume(_ buffer: AVAudioPCMBuffer, converter: AVAudioConverter, target: AVAudioFormat) {
        let ratio = target.sampleRate / buffer.format.sampleRate
        let capacity = AVAudioFrameCount(Double(buffer.frameLength) * ratio) + 16
        guard let out = AVAudioPCMBuffer(pcmFormat: target, frameCapacity: capacity) else { return }
        var handed = false
        var error: NSError?
        _ = converter.convert(to: out, error: &error) { _, status in
            if handed { status.pointee = .noDataNow; return nil }
            handed = true
            status.pointee = .haveData
            return buffer
        }
        guard error == nil, out.frameLength > 0, let channel = out.int16ChannelData else { return }
        let bytes = Data(bytes: channel[0], count: Int(out.frameLength) * 2)
        var seconds = 0.0
        var full = false
        lock.lock()
        if running {
            pcm.append(bytes)
            if pcm.count >= limitBytes {
                pcm = pcm.prefix(limitBytes)
                full = true
                running = false
            }
            seconds = Double(pcm.count) / 2 / AudioRecorder.sampleRate
        }
        lock.unlock()
        progress?(seconds)
        if full { limitReached?() }
    }

    /// The engine's input changed under a hold (a headset came or went): the hold ends and the owner is told.
    private func routeChanged() {
        lock.lock()
        let wasRunning = running
        running = false
        armed = false
        pcm = Data()
        lock.unlock()
        guard wasRunning else { return }
        engine.inputNode.removeTap(onBus: 0)
        engine.stop()
        failed?("The microphone changed (a headset connected or disconnected). Hold the microphone again.")
    }

    /// The recording so far, and the microphone released.
    func stop() -> Data {
        lock.lock()
        armed = false
        running = false
        let result = pcm
        pcm = Data()
        lock.unlock()
        engine.inputNode.removeTap(onBus: 0)
        engine.stop()
        return result
    }

    func cancel() { _ = stop() }
}
