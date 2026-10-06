import AppIntents
import Foundation

// "Hey Siri, ask JARVIS" and "Hey Siri, stop JARVIS" (the owner's "can we add siri to the next build", 2026-10-06).
// App Intents in the app itself: no extra Xcode target, nothing to switch on. Siri learns the phrases once the app
// has run on the phone. The question goes to the one Core as if typed on the Ask screen; the reply is shown and
// spoken by the app in JARVIS's voice, not by Siri (the Core's answers take longer than Siri waits for a spoken
// reply, and the voice is JARVIS's own).

/// Siri asks "What should I ask JARVIS?", opens the app, and the app sends the question and speaks the reply.
struct AskJarvisIntent: AppIntent {
    static var title: LocalizedStringResource = "Ask JARVIS"
    static var description = IntentDescription("Sends a question to your JARVIS Core; the app shows and speaks the reply.")
    static var openAppWhenRun: Bool = true

    @Parameter(title: "Question", requestValueDialog: "What should I ask JARVIS?")
    var question: String

    @MainActor
    func perform() async throws -> some IntentResult & ProvidesDialog {
        let text = question.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { throw $question.needsValueError("What should I ask JARVIS?") }
        guard AppSettings.address != nil, Keychain.read() != nil else {
            return .result(dialog: "This phone is not paired with JARVIS yet. Open the app and pair it first.")
        }
        // The app is opening (or already in front): it takes the question from here, once unlocked.
        AppSettings.siriQuestionAt = Date()
        AppSettings.siriQuestion = text
        NotificationCenter.default.post(name: .jarvisSiriQuestion, object: nil)
        return .result(dialog: "Asking JARVIS.")
    }
}

/// The emergency stop from Siri, without opening the app. As everywhere: any paired device may stop everything,
/// and only RESUME on the PC lifts it.
struct StopJarvisIntent: AppIntent {
    static var title: LocalizedStringResource = "Stop JARVIS"
    static var description = IntentDescription("Raises JARVIS's emergency stop on the PC. Only RESUME on the PC lifts it.")
    static var openAppWhenRun: Bool = false

    @MainActor
    func perform() async throws -> some IntentResult & ProvidesDialog {
        guard let address = AppSettings.address, let credential = Keychain.read() else {
            return .result(dialog: "This phone is not paired with JARVIS yet.")
        }
        let client = HTTPCoreClient(address: address, credential: credential)
        do {
            _ = try await client.stop()
            return .result(dialog: "JARVIS is stopped. Press RESUME on the PC to continue.")
        } catch {
            let sentence = (error as? ClientFailure)?.errorDescription ?? "JARVIS could not be reached."
            return .result(dialog: IntentDialog(stringLiteral: sentence))
        }
    }
}

/// The phrases Siri answers to. `.applicationName` is the app's name on the phone, JARVIS.
struct JarvisShortcuts: AppShortcutsProvider {
    static var appShortcuts: [AppShortcut] {
        AppShortcut(intent: AskJarvisIntent(),
                    phrases: ["Ask \(.applicationName)", "Ask \(.applicationName) a question", "Talk to \(.applicationName)"],
                    shortTitle: "Ask JARVIS",
                    systemImageName: "waveform.circle")
        AppShortcut(intent: StopJarvisIntent(),
                    phrases: ["Stop \(.applicationName)", "\(.applicationName) emergency stop", "Stop everything on \(.applicationName)"],
                    shortTitle: "Stop JARVIS",
                    systemImageName: "octagon.fill")
    }
    static var shortcutTileColor: ShortcutTileColor = .navy
}

extension Notification.Name {
    /// Posted by the Ask intent when the app is already running, so the question is sent without waiting for a
    /// scene change.
    static let jarvisSiriQuestion = Notification.Name("com.teagueindustries.jarvis.siri-question")
}
