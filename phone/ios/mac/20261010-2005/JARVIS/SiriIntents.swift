import AppIntents
import Foundation
import WidgetKit

// "Hey Siri, ask JARVIS" and "Hey Siri, stop JARVIS" (the owner's "can we add siri to the next build", 2026-10-06).
// App Intents in the app itself: no extra Xcode target, nothing to switch on. Siri learns the phrases once the app
// has run on the phone.

/// "Hey Siri, ask JARVIS" (round 6, item 13: the owner's "can we also implement that I can use jarvis and no require
/// to be in the app to use it", 2026-10-10). Siri asks "What should I ask JARVIS?", the question goes to the one
/// Core, and Siri shows and says the reply without opening the app. Only on an unlocked iPhone: from the lock screen
/// Siri asks for Face ID or the passcode first, as JARVIS's answers are the owner's; and not while the app's own
/// "Lock with Face ID" is on, which Siri cannot ask for (it would let anyone holding the unlocked phone past it).
/// The question and the reply go into the conversation the Ask screen continues, which reads them from the Core when
/// it is next shown. Siri says the reply in its own voice; the app speaks in JARVIS's. Also an action for the
/// Shortcuts app: its value is the whole reply as plain words (or the sentence saying why there is none), for a
/// following "Speak Text" or "Show Result".
struct AskJarvisIntent: AppIntent {
    static var title: LocalizedStringResource = "Ask JARVIS"
    static var description = IntentDescription("Sends a question to your JARVIS Core and gives the reply here, without opening the app.")
    static var openAppWhenRun: Bool = false
    static var authenticationPolicy: IntentAuthenticationPolicy = .requiresAuthentication

    /// How long Siri waits for the reply, in all. Later the Core goes on, and the reply is in the app's conversation.
    static let wait: TimeInterval = 24
    static let lockedSentence = "The JARVIS lock is on, so Siri cannot answer here. Open JARVIS to ask, or turn off Lock with Face ID in its Phone settings to let Siri answer."
    /// About how much of a reply Siri says; the whole reply is in the app and in the action's value.
    static let spokenLimit = 1_200

    @Parameter(title: "Question", requestValueDialog: "What should I ask JARVIS?")
    var question: String

    @MainActor
    func perform() async throws -> some IntentResult & ReturnsValue<String> & ProvidesDialog {
        let text = question.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { throw $question.needsValueError("What should I ask JARVIS?") }
        let answer = await ask(text)
        return .result(value: answer.value, dialog: IntentDialog(stringLiteral: answer.said))
    }

    /// The reply (`value`, whole) and what Siri says (`said`: the reply as plain words, or why there is none).
    @MainActor
    private func ask(_ text: String) async -> (value: String, said: String) {
        func sentence(_ words: String) -> (value: String, said: String) { (words, words) }
        guard text.unicodeScalars.count <= 12_000 else { return sentence("That is more than 12,000 characters. Shorten it.") }
        guard let address = AppSettings.address, let key = Keychain.read(), let deviceId = AppSettings.deviceId else {
            return sentence("This phone is not paired with JARVIS yet. Open the app and pair it first.")
        }
        guard !AppSettings.lockEnabled else { return sentence(Self.lockedSentence) }
        // The conversation the Ask screen continues, kept so the app shows this exchange when it is opened. While a
        // question of the app's own is still on its way (the app left the front before its reply), Siri's question
        // goes into a conversation of its own instead, never mixed into that one.
        let live = SessionModel.live
        let conversation: String
        if let live, live.busy || live.recording {
            conversation = ConversationIds.new(deviceId: deviceId)
        } else {
            conversation = live?.conversation ?? AppSettings.conversation ?? ConversationIds.new(deviceId: deviceId)
            AppSettings.conversation = conversation
        }
        let client = HTTPCoreClient(address: address, credential: key)
        let outcome: OneQuestion.Outcome
        do {
            outcome = try await OneQuestion.ask(client, text: text, conversation: conversation,
                                                location: live?.questionLocation, waitAtMost: Self.wait)
        } catch {
            // Not reached, the emergency stop, busy, a refused key: the Core's or the app's own sentence. The app
            // acts on a refused key itself at its next hello.
            return sentence((error as? ClientFailure)?.errorDescription ?? "JARVIS could not be reached.")
        }
        live?.exchangedOutside(in: conversation)   // the Ask screen reads its lines again from the Core
        switch outcome {
        case .reply(let reply):
            let words = PlainWords.from(reply)   // as plain words for Siri and for a shortcut's Speak Text alike
            let spoken = PlainWords.short(words, limit: Self.spokenLimit)
            return (words, spoken.cut ? spoken.text + " The whole reply is in JARVIS." : spoken.text)
        case .failed(let failure):
            return sentence(failure)
        case .cancelled:
            // Not asked for from here: most likely the emergency stop on the PC. The Core's status says, quickly.
            if let info = try? await client.status(timeout: 4), info.stopped {
                return sentence("JARVIS is stopped. Press RESUME on the PC to continue.")
            }
            return sentence("The question was cancelled on the PC.")
        case .stillWorking:
            return sentence("JARVIS is still working on that. The reply will be in the app.")
        case .linkLost:
            return sentence("The connection dropped while JARVIS was answering. The reply will be in the app.")
        case .noReply:
            return sentence("JARVIS finished without a reply.")
        }
    }
}

/// "Hey Siri, talk to JARVIS" (round 6): opens the app in a hands-free conversation, the same request as the lock
/// screen's button (OpenJarvisListeningIntent): JARVIS listens, answers and listens again until "thank you Jarvis".
struct TalkToJarvisIntent: AppIntent {
    static var title: LocalizedStringResource = "Talk to JARVIS"
    static var description = IntentDescription("Opens JARVIS in a hands-free conversation: speak, and JARVIS answers and listens again.")
    static var openAppWhenRun: Bool = true

    @MainActor
    func perform() async throws -> some IntentResult {
        UserDefaults.standard.set(Date(), forKey: OpenJarvisListeningIntent.requestKey)
        NotificationCenter.default.post(name: OpenJarvisListeningIntent.requestNotification, object: nil)
        return .result()
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
            WidgetCenter.shared.reloadTimelines(ofKind: WidgetKinds.status)   // the widget says Stopped soon, not in 15 minutes
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
        AppShortcut(intent: TalkToJarvisIntent(),
                    phrases: ["Talk to \(.applicationName)", "Start a conversation with \(.applicationName)", "Chat with \(.applicationName)"],
                    shortTitle: "Talk to JARVIS",
                    systemImageName: "bubble.left.and.text.bubble.right")
        AppShortcut(intent: AskJarvisIntent(),
                    phrases: ["Ask \(.applicationName)", "Ask \(.applicationName) a question"],
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
