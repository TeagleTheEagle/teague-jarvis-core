import AVFoundation
import Foundation

/// Plays the sound the Core returns for a reply (MP3 or WAV, whichever voice the owner uses) and waits for its end.
/// Lives on the main actor, as the session does, so a stop and a finish never race. A call or another app's sound
/// pauses the reply; it goes on afterwards when iOS says it may, and ends otherwise (the text is on screen). A
/// headset that goes away ends it too: nothing plays on from the speaker unasked.
@MainActor
final class AudioPlayer: NSObject, AVAudioPlayerDelegate {
    private var player: AVAudioPlayer?
    private var finished: CheckedContinuation<Void, Error>?
    private var observers: [NSObjectProtocol] = []

    override init() {
        super.init()
        let center = NotificationCenter.default
        observers.append(center.addObserver(forName: AVAudioSession.interruptionNotification, object: nil, queue: .main) { [weak self] note in
            let type = (note.userInfo?[AVAudioSessionInterruptionTypeKey] as? UInt).flatMap(AVAudioSession.InterruptionType.init(rawValue:))
            let options = AVAudioSession.InterruptionOptions(rawValue: (note.userInfo?[AVAudioSessionInterruptionOptionKey] as? UInt) ?? 0)
            Task { @MainActor in self?.interrupted(type, options: options) }
        })
        observers.append(center.addObserver(forName: AVAudioSession.routeChangeNotification, object: nil, queue: .main) { [weak self] note in
            let reason = (note.userInfo?[AVAudioSessionRouteChangeReasonKey] as? UInt).flatMap(AVAudioSession.RouteChangeReason.init(rawValue:))
            Task { @MainActor in self?.routeChanged(reason) }
        })
    }

    deinit {
        for observer in observers { NotificationCenter.default.removeObserver(observer) }
    }

    func play(_ sound: Data) async throws {
        stop()
        let session = AVAudioSession.sharedInstance()
        try session.setCategory(.playAndRecord, mode: .default, options: AudioRecorder.sessionOptions)
        try session.setActive(true)
        let player = try AVAudioPlayer(data: sound)
        player.delegate = self
        self.player = player
        try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<Void, Error>) in
            finished = continuation
            if !(player.prepareToPlay() && player.play()) {
                self.player = nil
                finish(with: PlaybackFailure.couldNotStart)
            }
        }
    }

    func stop() {
        player?.stop()
        player = nil
        finish(with: nil)
    }

    /// Resumes the waiting caller exactly once.
    private func finish(with error: Error?) {
        guard let continuation = finished else { return }
        finished = nil
        if let error { continuation.resume(throwing: error) } else { continuation.resume() }
    }

    private func interrupted(_ type: AVAudioSession.InterruptionType?, options: AVAudioSession.InterruptionOptions) {
        guard let type, player != nil else { return }
        switch type {
        case .began:
            break   // iOS has paused the sound; the caller keeps waiting for the end
        case .ended:
            if options.contains(.shouldResume), let player {
                try? AVAudioSession.sharedInstance().setActive(true)
                if player.play() { return }
            }
            stop()
        @unknown default:
            break
        }
    }

    private func routeChanged(_ reason: AVAudioSession.RouteChangeReason?) {
        if reason == .oldDeviceUnavailable { stop() }
    }

    nonisolated func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) {
        Task { @MainActor in
            self.player = nil
            self.finish(with: nil)
        }
    }

    nonisolated func audioPlayerDecodeErrorDidOccur(_ player: AVAudioPlayer, error: Error?) {
        let reason = error?.localizedDescription
        Task { @MainActor in
            self.player = nil
            self.finish(with: PlaybackFailure.decodeFailed(reason))
        }
    }

    enum PlaybackFailure: Error, LocalizedError {
        case couldNotStart
        case decodeFailed(String?)
        var errorDescription: String? {
            switch self {
            case .couldNotStart: return "The reply's sound could not be played."
            case .decodeFailed: return "The reply's sound could not be read."
            }
        }
    }
}
