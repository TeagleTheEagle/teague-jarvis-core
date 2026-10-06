import AVFoundation
import Foundation

/// Plays the sound the Core returns for a reply (MP3 or WAV, whichever voice the owner uses) and waits for its end.
/// Lives on the main actor, as the session does, so a stop and a finish never race.
@MainActor
final class AudioPlayer: NSObject, AVAudioPlayerDelegate {
    private var player: AVAudioPlayer?
    private var finished: CheckedContinuation<Void, Error>?

    func play(_ sound: Data) async throws {
        stop()
        let session = AVAudioSession.sharedInstance()
        try session.setCategory(.playAndRecord, mode: .default, options: [.defaultToSpeaker])
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
