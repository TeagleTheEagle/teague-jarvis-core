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

/// "Announce to JARVIS" (round 5, R4): for a Shortcuts automation the owner sets up ("When I get a message from
/// Jack" > run this with the sender and the text). The PC speaks it in JARVIS's voice ("Mr Teague, Jack texted
/// you: ...") and lists it in the notices. Runs without opening the app; nothing is kept on the phone.
struct AnnounceToJarvisIntent: AppIntent {
    static var title: LocalizedStringResource = "Announce to JARVIS"
    static var description = IntentDescription("Tells JARVIS on the PC to announce a message: who it is from and what it says.")
    static var openAppWhenRun: Bool = false

    @Parameter(title: "From", requestValueDialog: "Who is it from?")
    var sender: String

    @Parameter(title: "Message", requestValueDialog: "What does it say?")
    var text: String

    @Parameter(title: "Kind", default: .text)
    var kind: AnnouncementKind

    @MainActor
    func perform() async throws -> some IntentResult & ProvidesDialog {
        guard let address = AppSettings.address, let credential = Keychain.read() else {
            return .result(dialog: "This phone is not paired with JARVIS yet.")
        }
        let who = AnnounceToJarvisIntent.announceable(sender)
        let what = AnnounceToJarvisIntent.announceable(text)
        guard !who.isEmpty else { throw $sender.needsValueError("Who is it from?") }
        guard !what.isEmpty else { return .result(dialog: "The message has no text to announce.") }   // a photo alone
        let client = HTTPCoreClient(address: address, credential: credential)
        do {
            let answer = try await client.announce(sender: who, text: what, kind: kind.rawValue)
            if !answer.announced { return .result(dialog: "JARVIS did not take the announcement.") }
            // `spoken`: the PC took the words to say aloud (its voice on, quiet hours off, nothing already queued).
            return .result(dialog: answer.spoken ? "Announced by JARVIS." : "JARVIS has it as a notice; the PC did not say it aloud.")
        } catch {
            let failure = error as? ClientFailure
            if failure?.notOnThisCore ?? false {
                return .result(dialog: "Announcements need JARVIS release 1.0.17 on the PC.")
            }
            return .result(dialog: IntentDialog(stringLiteral: failure?.errorDescription ?? "JARVIS could not be reached."))
        }
    }

    /// The words as the Core takes them. The Core refuses an announcement holding any character whose Unicode
    /// general category starts with C (controls, format, surrogates, private use, unassigned) by its own tables,
    /// Unicode 15.0 in 1.0.17 (docs/MAC-ANSWERS-20261010.md, item 2), with "Invalid announcement.". A text message
    /// often has line breaks and emoji joined by zero-width joiners, and may have emoji newer than Unicode 15.0.
    /// So: line breaks, tabs, other controls and separators become one plain space; format, surrogate, private-use
    /// and unassigned characters, every character newer than Unicode 15.0 (unassigned on the Core), and Messages'
    /// attachment marker (U+FFFC, a photo) are taken out; the ends are trimmed. Everything the Core accepts stays as
    /// it is: accents, apostrophes, variation selectors (the emoji style), skin tones, flags of two letters, keycaps.
    /// An emoji made of several joined ones comes apart into its parts.
    static func announceable(_ raw: String) -> String {
        var kept = String.UnicodeScalarView()
        var lastWasSpace = true   // no space at the start
        for scalar in raw.precomposedStringWithCanonicalMapping.unicodeScalars {
            let properties = scalar.properties
            switch properties.generalCategory {
            case .control, .spaceSeparator, .lineSeparator, .paragraphSeparator:
                if !lastWasSpace { kept.append(" "); lastWasSpace = true }
            case .format, .privateUse, .surrogate, .unassigned:
                continue
            default:
                guard let age = properties.age, (age.major, age.minor) <= (15, 0) else { continue }   // unknown to the Core
                if scalar.value == 0xFFFC { continue }
                kept.append(scalar)
                lastWasSpace = false
            }
        }
        return String(kept).trimmingCharacters(in: .whitespaces)
    }
}

/// The Core's three kinds of announcement.
enum AnnouncementKind: String, AppEnum {
    case text, call, other
    static var typeDisplayRepresentation = TypeDisplayRepresentation(name: "Kind")
    static var caseDisplayRepresentations: [AnnouncementKind: DisplayRepresentation] = [
        .text: "Text message", .call: "Call", .other: "Other"
    ]
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
        // R4 by hand as well as from a Shortcuts automation: Siri (or the tile in the Shortcuts app) asks who it is
        // from and what it says; the PC says it aloud and keeps it as a notice.
        AppShortcut(intent: AnnounceToJarvisIntent(),
                    phrases: ["Announce to \(.applicationName)", "Send an announcement to \(.applicationName)"],
                    shortTitle: "Announce to JARVIS",
                    systemImageName: "megaphone")
    }
    static var shortcutTileColor: ShortcutTileColor = .navy
}

extension Notification.Name {
    /// Posted by the Ask intent when the app is already running, so the question is sent without waiting for a
    /// scene change.
    static let jarvisSiriQuestion = Notification.Name("com.teagueindustries.jarvis.siri-question")
}
