import Foundation
import Combine
import UIKit
import AVFoundation
import LocalAuthentication

/// What the phone is doing with the one Core: paired or not, the conversation in progress, the question running,
/// what the Core said. Every change of what is saved happens on the PC; this is the screen's copy.
@MainActor
final class SessionModel: ObservableObject {
    @Published private(set) var state: JarvisState = .offline {
        // The screen stays awake while JARVIS listens, thinks, works or speaks; the phone's own timer otherwise.
        didSet { UIApplication.shared.isIdleTimerDisabled = SessionModel.awakeStates.contains(state) }
    }
    @Published private(set) var paired = false
    @Published private(set) var info: DeviceInfo?
    @Published private(set) var lines: [ChatLine] = []
    @Published private(set) var notice: String?          // the Core's sentence, or why something did not happen
    @Published private(set) var busy = false              // a question is running on the PC
    @Published private(set) var stopped = false {         // the emergency stop holds on the PC
        // When a later hello, status or metrics reading says the stop has lifted, the stop's note goes with it
        // (docs/PHONE-V1-RESULT.md, item 7).
        didSet {
            if oldValue && !stopped, let note = notice, note.localizedCaseInsensitiveContains("emergency stop") { notice = nil }
            if stopped && !oldValue { approvals = [] }   // the stop drops every waiting approval on the Core
        }
    }
    @Published private(set) var toolName: String?
    /// The reply as it is being written on the PC (Core 1.0.17, `assistant.draft`: each event carries the whole
    /// text so far; an empty text takes it away). Shown, never spoken; the finished reply replaces it.
    @Published private(set) var writing: String?
    /// A question made while the Core could not be reached, waiting on the phone for the link (hold-and-send).
    @Published private(set) var held: HeldQuestion?
    private var heldSince: Date?   // when the wait began; a re-hold after a failed attempt does not restart the clock
    @Published private(set) var recording = false
    @Published private(set) var recordingSeconds = 0.0
    /// Hands-free listening (the lock-screen and Control Center button, round 4): the recording was started by
    /// jarvis://listen, not by a held finger, so it ends by itself at a pause after speech, or at a tap on the
    /// microphone, or at the 30 s limit.
    @Published private(set) var handsFree = false
    /// The Ask screen is wanted in front (a button or link opened the app): MainTabs switches to it on change.
    @Published private(set) var askRequested = 0
    private var pendingHandsFree = false     // a button press waiting for the front, the unlock or the Core's hello
    private var pendingHandsFreeAt: Date?
    private var inFront = false              // the scene is active: set by cameToFront, cleared when inactive or in the background
    private var heardSpeech = false
    private var lastLoudAt = Date()
    private var levelFloor: Double?          // the quietest buffer of this recording (the room), for the speech threshold
    @Published private(set) var roundTripMs: Int?         // the phone's own round trip of the last hello, status or metrics call
    @Published private(set) var roundTripAt: Date?
    @Published private(set) var reached = false           // the last request got an answer from the Core
    @Published private(set) var conversation: String
    @Published private(set) var address: CoreAddress?
    @Published private(set) var deviceName: String?
    @Published private(set) var metrics: Metrics?          // the PC's health, as the dashboard has it
    @Published private(set) var overview: Overview?        // open tasks, projects, the day's reminders
    @Published private(set) var healthNote: String?
    /// The last health readings while a screen polls (ROUND3-COMMAND-LOOK.md): the Overview's sparklines.
    @Published private(set) var healthHistory: [HealthSample] = []
    /// The microphone level trace (0 to 1 each) of the current or last hold: the Overview's waveform, the orb's glow.
    @Published private(set) var micLevels: [Double] = []
    @Published private(set) var locked = false            // Face ID (or the passcode) before the screens show
    @Published var draft = ""
    @Published var speakReplies: Bool {
        didSet {
            AppSettings.speakReplies = speakReplies
            if !speakReplies { player.stop() }   // muted mid-reply: the voice stops; the text stays
        }
    }
    @Published var lockEnabled: Bool {
        didSet {
            AppSettings.lockEnabled = lockEnabled
            if !lockEnabled { locked = false }
        }
    }
    /// "Send my location with questions" (round 5, R3): off by default; while on, a fix no older than two minutes
    /// goes with each question and the Core keeps nothing unless asked to remember.
    @Published var sendLocation: Bool {
        didSet {
            AppSettings.sendLocation = sendLocation
            if sendLocation { locations.start() } else { locations.stop() }
        }
    }
    let locations = LocationProvider()

    // Core 1.0.17 (docs/MAC-REQUESTS-20261007.md): what this Core serves and what it has for this phone.
    enum Availability: Equatable { case unknown, notOnThisCore, notAllowed, ready }
    @Published private(set) var approvals: [ApprovalItem] = []
    @Published private(set) var approvalsAvailability: Availability = .unknown
    /// What came of the last answers (newest first, five kept): shown under the list as receipts.
    @Published private(set) var approvalOutcomes: [ApprovalOutcome] = []
    @Published private(set) var noticeItems: [NoticeItem] = []
    @Published private(set) var noticesAvailability: Availability = .unknown
    /// Why the first read of the approvals or the notices gave nothing (the Core's sentence), shown in the sheet
    /// instead of an endless "Reading…".
    @Published private(set) var approvalsFailure: String?
    @Published private(set) var noticesFailure: String?
    @Published private(set) var deviceList: DeviceList?
    @Published private(set) var devicesAvailability: Availability = .unknown
    private var devicesCheckedOnCore: String?   // the Core version the "not on this Core yet" answer came from

    /// The owner's tick "May use this PC's tools" for this phone, as the Core reports it.
    var tools: Bool { info?.tools ?? false }
    /// The owner's tick "May approve for JARVIS" for this phone.
    var mayApprove: Bool { info?.approve ?? false }
    /// Approvals waiting for an answer (0 unless the tick is on).
    var waitingApprovals: Int { info?.waiting ?? 0 }
    /// Notices this phone has not read yet.
    var unreadNotices: Int { info?.notices ?? 0 }

    let client: HTTPCoreClient
    private let recorder = AudioRecorder()
    private let player = AudioPlayer()
    private let replyHaptic = UINotificationFeedbackGenerator()
    private let holdHaptic = UIImpactFeedbackGenerator(style: .medium)
    private var work: Task<Void, Never>?
    private var healthTask: Task<Void, Never>?
    private var runId: String?
    private var generation = 0
    /// A question whose answer the phone lost the link to (switched apps, no signal): the Core keeps the answer,
    /// and the phone picks it up when the link is back.
    private var resumable: (runId: String, after: Int)?
    /// After a relaunch the conversation id comes back from the settings; its lines are read from the Core at the
    /// first hello, so the Ask screen shows where the conversation stood (check 3 of the phone plan).
    private var historyPending: Bool
    /// An approval was applied while a question ran: the Core's "Approved from ..." line is read when the run ends.
    private var rereadAfterRun = false
    private var reloadingLines = false   // a read of the restored conversation is on its way
    private var historyReadFailures = 0  // failed reads of the restored conversation; given up after five
    private var hiddenAt: Date?
    private var unlocking = false
    private var observers: [NSObjectProtocol] = []
    private var cancellables = Set<AnyCancellable>()
    private static let awakeStates: Set<JarvisState> = [.listening, .thinking, .executing, .speaking]
    /// Back within a minute (a call, the control centre, another app for a moment): no second Face ID.
    static let lockGraceSeconds: TimeInterval = 60
    /// A question Siri took is sent only within this time; later (the lock left on its screen, the app not opened)
    /// it is dropped and said so, never sent into a later conversation unasked.
    static let siriQuestionMaxAge: TimeInterval = 120
    /// A held question is sent when the link returns within this time; later it is dropped and said so, so that
    /// nothing goes to the Core long after the owner asked it, into a moment they are no longer in.
    static let heldQuestionMaxAge: TimeInterval = 15 * 60

    init() {
        let address = AppSettings.address
        let credential = Keychain.read()
        self.address = address
        self.deviceName = AppSettings.deviceName
        self.paired = address != nil && credential != nil && AppSettings.deviceId != nil
        let restored = AppSettings.conversation
        self.conversation = restored ?? SessionModel.newConversationId(deviceId: AppSettings.deviceId)
        self.historyPending = restored != nil
        self.speakReplies = AppSettings.speakReplies
        self.lockEnabled = AppSettings.lockEnabled
        self.sendLocation = AppSettings.sendLocation
        self.client = HTTPCoreClient(address: address, credential: credential)
        self.locked = self.paired && self.lockEnabled   // on open: locked until Face ID or the passcode
        watchAudio()
        watchSiri()
        watchListenRequests()
        // The settings sheet watches the session: a change in the location provider (iOS denying it) redraws at once.
        locations.objectWillChange.sink { [weak self] _ in self?.objectWillChange.send() }.store(in: &cancellables)
        if sendLocation { locations.start() }   // the switch was on when the app last closed
    }

    deinit {
        for observer in observers { NotificationCenter.default.removeObserver(observer) }
    }

    // MARK: pairing

    /// Pair with the code the owner read from the PC. The key is kept in the Keychain and never shown again.
    func pair(host: String, port: Int, code: String) async throws {
        let address = CoreAddress(host: host, port: port)
        guard address.baseURL != nil else { throw ClientFailure.invalidAddress }
        let digits = code.filter(\.isNumber)
        guard digits.count == 8 else { throw ClientFailure.rejected("The code has eight digits.") }
        let paired = try await client.pair(address: address, code: digits, capabilities: Capability.declared)
        guard Keychain.write(paired.credential) else {
            // The code is used up and the PC lists the device: the owner starts a new pairing there.
            throw ClientFailure.unavailable("The key could not be kept on this phone. Start the pairing again on the PC.")
        }
        AppSettings.address = address
        AppSettings.deviceId = paired.deviceId
        AppSettings.deviceName = paired.name
        client.address = address
        client.credential = paired.credential
        self.address = address
        self.deviceName = paired.name
        self.paired = true
        self.notice = nil
        newConversation()
        await connect()
    }

    func forgetPairing() {
        interrupt()
        stopHealthPolling()
        AppSettings.forgetPairing()
        client.credential = nil
        paired = false
        locked = false
        historyPending = false
        clearCoreData()
        state = .offline
        notice = nil
    }

    /// Everything on screen that came from the Core of a pairing that is over: cleared the same way whether the
    /// owner forgot the pairing or the Core refused the key (review of round 3, finding 12).
    private func clearCoreData() {
        info = nil
        metrics = nil
        overview = nil
        healthHistory = []
        micLevels = []
        writing = nil
        held = nil
        heldSince = nil
        lines = []
        approvals = []
        approvalOutcomes = []
        approvalsAvailability = .unknown
        approvalsFailure = nil
        noticeItems = []
        noticesAvailability = .unknown
        noticesFailure = nil
        deviceList = nil
        devicesAvailability = .unknown
        devicesCheckedOnCore = nil
    }

    // MARK: the Core

    /// Say hello: who this phone is and what the owner allows; whether the emergency stop holds. Then a question
    /// Siri took (reached or not: it is sent, and held on the phone when the Core cannot be reached), the lines of
    /// a restored conversation, an answer the phone lost the link to, and a held question when the link is back.
    func connect() async {
        guard paired else { state = .offline; return }
        let started = Date()
        var reachedCore = false
        do {
            let info = try await client.hello(capabilities: Capability.declared)
            self.info = info
            self.deviceName = info.name
            self.stopped = info.stopped
            if state == .offline || state == .error { notice = nil }   // a failure's sentence; any other note stays until the next action
            noteReached(since: started)
            if !busy && !recording { state = info.stopped ? .stopped : .idle }   // a hello mid-recording leaves LISTENING alone
            reachedCore = true
            startPendingHandsFreeIfReady()   // a button press that waited for this hello
        } catch {
            fail(error)
            pendingHandsFree = false   // the press cannot be served: the "cannot be reached" sentence is on screen
            pendingHandsFreeAt = nil
        }
        pickUpSiriQuestion()
        guard reachedCore else { return }
        if !busy {
            await reloadLinesIfPending()
            if let resumable, !locked {   // never spoken over the lock screen: picked up once unlocked
                await resume(resumable)
            }
        }
        await releaseHeld()
    }

    /// The lines of the conversation in progress, read from the Core (the route Chats uses): after a relaunch the
    /// Ask screen shows where the conversation stood, not a fresh one. Tried at the hello and again at every status
    /// and health reading until one read succeeds: a single failed read at the start (the link not yet up, the Core
    /// busy with another request of this phone) no longer leaves the screen empty for the whole session (seen on
    /// 2026-10-10 against Core 1.0.17: two of three relaunches came up empty).
    private func reloadLinesIfPending() async {
        guard historyPending, !busy, !recording, !reloadingLines else { return }
        guard lines.isEmpty else { historyPending = false; return }   // a new line is on screen already: nothing to restore
        reloadingLines = true
        defer { reloadingLines = false }
        let id = conversation
        let ticket = generation
        let history: ConversationHistory
        do {
            history = try await client.history(conversation: id, limit: 100)
        } catch {
            // The Core refused this conversation (its two sentences for that): nothing to restore, not asked again.
            // Anything else (no link, busy, the request limit, not ready) is tried again at the next reading, five
            // failed reads at most.
            if case .rejected(let sentence)? = error as? ClientFailure,
               sentence == "Wearable conversation required." || sentence == "Unknown fields." {
                historyPending = false
            } else if (error as? ClientFailure) != .unreachable {
                historyReadFailures += 1
                if historyReadFailures >= 5 { historyPending = false }
            }
            return
        }
        guard generation == ticket, conversation == id, historyPending else { return }
        historyPending = false
        guard !busy, lines.isEmpty else { return }
        lines = history.messages.map { ChatLine(isUser: $0.role == "user", text: $0.content) }.suffix(80).map { $0 }
    }

    /// A cheap round trip, for the Overview's link time, the stop state and the 1.0.17 counts. `quiet` is the
    /// polling form: a failure goes to the health note, as the metrics reads do, instead of overwriting the Ask
    /// screen's sentence every ten seconds.
    func checkStatus(quiet: Bool = false) async {
        guard paired else { return }
        let started = Date()
        do {
            let info = try await client.status()
            self.info = info
            self.stopped = info.stopped
            noteReached(since: started)
            if !busy && state != .speaking && state != .listening { state = info.stopped ? .stopped : .idle }
            await reloadLinesIfPending()   // a restored conversation whose first read failed
            await releaseHeld()
        } catch {
            if quiet {
                if !SessionModel.isBusy(error) { healthNote = report(error) }   // busy: the next status follows in 10 s
                if (error as? ClientFailure) == .unreachable, !busy, !recording { state = .offline }
            } else {
                fail(error)
            }
        }
    }

    private func noteReached(since started: Date) {
        reached = true
        roundTripMs = Int(Date().timeIntervalSince(started) * 1000)
        roundTripAt = Date()
    }

    // MARK: hold-and-send

    static let heldNotice = "One question is already held for the Core. DROP it, or wait for the link."

    /// The Core could not be reached when the question was made: keep it, say so, and wait for the link. One
    /// question at most; a second one is refused while one waits. The clock of the wait starts at the first hold
    /// and is not restarted by a later failed attempt.
    private func hold(_ question: HeldQuestion) {
        held = question
        if heldSince == nil { heldSince = Date() }
        reached = false
        state = .offline
        notice = "Your question is held on this phone and goes when the link is back. DROP or NEW CHAT drops it."
    }

    /// The owner does not want the held question sent after all.
    func dropHeld() {
        guard held != nil else { return }
        held = nil
        heldSince = nil
        notice = nil
        state = reached ? (stopped ? .stopped : .idle) : .offline
    }

    /// The link is back (a hello, status or health reading answered): send the held question, or drop it when too
    /// old. Called by those three at their end, never over the lock screen (the reply would arrive unseen and
    /// unspoken). Typed words are first looked for in the conversation on the Core: a `start` whose body got
    /// through just before the link dropped has already been answered there, and must not run twice.
    private func releaseHeld() async {
        guard let question = held, paired, !busy, !recording, !locked else { return }
        held = nil
        let since = heldSince ?? Date()
        heldSince = nil
        guard Date().timeIntervalSince(since) <= SessionModel.heldQuestionMaxAge else {
            notice = "Your held question was dropped: the link came back more than \(Int(SessionModel.heldQuestionMaxAge / 60)) minutes later. Ask again if you still want it."
            return
        }
        guard !stopped else {
            notice = "Your held question was dropped: the emergency stop is on. Press RESUME on the PC and ask again."
            return
        }
        notice = nil
        switch question {
        case .words(let text):
            if await alreadyAsked(text, since: since) {
                await refreshLinesFromCore()
                notice = "Your question had reached JARVIS before the link dropped; its reply is in the lines."
                return
            }
            send(text)
        case .voice(let pcm):
            transcribeAndSend(pcm)   // transcription has no side effect on the PC, so it may simply run again
        }
    }

    /// Whether the conversation on the Core already holds these words as a question asked since the hold began
    /// (a minute of slack for the two clocks). A failed read counts as "not asked": the question is then sent.
    private func alreadyAsked(_ text: String, since: Date) async -> Bool {
        guard let history = try? await client.history(conversation: conversation, limit: 5) else { return false }
        let from = since.timeIntervalSince1970 - 60
        return history.messages.contains { $0.role == "user" && $0.content == text && $0.created >= from }
    }

    /// The conversation's lines as the Core keeps them, replacing the screen's copy (used when a held question
    /// turns out to have been answered already).
    private func refreshLinesFromCore() async {
        let id = conversation
        let ticket = generation
        guard let history = try? await client.history(conversation: id, limit: 100) else { return }
        guard generation == ticket, conversation == id, !busy else { return }
        lines = history.messages.map { ChatLine(isUser: $0.role == "user", text: $0.content) }.suffix(80).map { $0 }
    }

    /// Ask the microphone permission once, early, so the system's question never arrives in the middle of a hold.
    func prepareMicrophone() {
        AudioRecorder.requestPermissionEarly()
    }

    // MARK: the PC's health (the Overview and the Ask screen's readouts)

    /// `metrics` (and now and then `overview`): the same numbers the dashboard shows, nothing new measured.
    func refreshHealth(overviewToo: Bool) async {
        guard paired else { return }
        let started = Date()
        do {
            let reading = try await client.metrics()
            metrics = reading
            stopped = reading.stopped
            healthNote = nil
            noteReached(since: started)
            appendHealthSample(reading)
            if overviewToo {
                overview = try await client.overview()
                await loadDevices()   // the device ecosystem panel, at the same pace as the overview
            }
            if !busy && state != .speaking && state != .listening { state = reading.stopped ? .stopped : .idle }
            await reloadLinesIfPending()
            await releaseHeld()
        } catch {
            if !SessionModel.isBusy(error) { healthNote = report(error) }   // busy: the next reading follows in 5 s
            if (error as? ClientFailure) == .unreachable, !busy { state = .offline }
        }
    }

    // MARK: Core 1.0.17: approvals, notices, devices (docs/MAC-REQUESTS-20261007.md)

    /// Whether an error means the op is not on this Core yet (an older Core's 400 "Operation unavailable.").
    private func notOnThisCore(_ error: Error) -> Bool { (error as? ClientFailure)?.notOnThisCore ?? false }

    /// The waiting list. On an older Core (no `approve` field in hello) nothing is asked; without the owner's tick
    /// the list is not available to this phone.
    func loadApprovals() async {
        guard paired, let info else { return }
        guard info.servesApprovals else { approvalsAvailability = .notOnThisCore; approvals = []; return }
        guard info.approve else { approvalsAvailability = .notAllowed; approvals = []; return }
        do {
            approvals = try await client.approvals()
            approvalsAvailability = .ready
            approvalsFailure = nil
        } catch {
            approvalsFailure = nil
            if notOnThisCore(error) { approvalsAvailability = .notOnThisCore; approvals = [] }
            else if SessionModel.isStopRefusal(error) {
                learnStop()   // nothing waits after a stop; the sheet says the stop is on and reads again after RESUME
                approvalsAvailability = .ready
            }
            else if case .notAllowed? = error as? ClientFailure { approvalsAvailability = .notAllowed; approvals = [] }
            else {
                let sentence = report(error)   // said in the sheet, where the owner is looking
                if paired { approvalsFailure = sentence }   // a refused key has cleared the Core's data: nothing kept
            }
        }
    }

    /// APPROVE: Face ID (or the passcode, iOS's fallback) first, always, whether or not the lock is on; on a failure
    /// or a cancel nothing is sent. Hidden while the emergency stop holds.
    func approve(_ item: ApprovalItem) async {
        guard mayApprove, !stopped else { return }
        let context = LAContext()
        context.localizedCancelTitle = "Not now"
        var unavailable: NSError?
        guard context.canEvaluatePolicy(.deviceOwnerAuthentication, error: &unavailable) else {
            record(ApprovalOutcome(id: item.id, label: item.label, sentence: "This phone has no passcode or Face ID set up, so nothing can be approved from it.", kind: .error))
            return
        }
        let passed = (try? await context.evaluatePolicy(.deviceOwnerAuthentication, localizedReason: "Approve for JARVIS: \(item.label)")) ?? false
        guard passed else { return }
        await answer(item, approving: true)
    }

    private func record(_ outcome: ApprovalOutcome) {
        approvalOutcomes.removeAll { $0.id == outcome.id }
        approvalOutcomes.insert(outcome, at: 0)
        if approvalOutcomes.count > 5 { approvalOutcomes.removeLast(approvalOutcomes.count - 5) }
    }

    /// REJECT needs no Face ID: it only stops something from happening.
    func reject(_ item: ApprovalItem) async {
        guard mayApprove else { return }
        await answer(item, approving: false)
    }

    private func answer(_ item: ApprovalItem, approving: Bool) async {
        do {
            let answer: ApprovalAnswer
            if approving { answer = try await client.approve(id: item.id) } else { answer = try await client.reject(id: item.id) }
            record(ApprovalOutcome(id: item.id, label: item.label, sentence: SessionModel.sentence(for: answer), kind: ApprovalOutcome.kind(of: answer.status)))
            approvals.removeAll { $0.id == item.id }
            // After "applied" the Core writes a line into the raising question's conversation: when that is this
            // phone's own conversation in progress, the lines are re-read so the receipt shows on Ask.
            if answer.status == "applied", item.conversation == conversation {
                if busy { rereadAfterRun = true } else { await refreshLinesFromCore() }   // a question running: read when it ends
            }
            await checkStatus(quiet: true)   // the waiting count
        } catch {
            // While the stop holds the Core answers with its stop sentence and has dropped the item; said in the
            // past tense, so the receipt stays true after RESUME.
            if SessionModel.isStopRefusal(error) {
                learnStop()
                record(ApprovalOutcome(id: item.id, label: item.label, sentence: "Not answered: the emergency stop was on and dropped this item.", kind: .error))
                return
            }
            record(ApprovalOutcome(id: item.id, label: item.label, sentence: report(error), kind: .error))
        }
    }

    static func sentence(for answer: ApprovalAnswer) -> String {
        let receipt = (answer.result ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
        switch answer.status {
        case "applied": return receipt.isEmpty ? "Applied." : "Applied. \(receipt)"
        case "failed": return receipt.isEmpty ? "Failed on the PC." : receipt   // the Core's one fixed sentence says it all

        case "denied": return "Rejected."
        case "expired": return "Expired before the answer arrived."
        case "unknown": return "The Core no longer has this item (answered elsewhere, or gone)."
        default: return "JARVIS answered \"\(answer.status)\"."
        }
    }

    /// The notices for this phone, newest first; reading them marks them read on the Core, and the count in the
    /// header goes to zero at the next status.
    func loadNotices() async {
        guard paired, let info else { return }
        guard info.servesNotices else { noticesAvailability = .notOnThisCore; noticeItems = []; return }
        do {
            let list = try await client.notices(after: nil)   // the whole list, newest first; reading marks it read on the Core
            noticeItems = list.items
            noticesAvailability = .ready
            noticesFailure = nil
            await checkStatus(quiet: true)   // the unread count goes to zero
        } catch {
            noticesFailure = nil
            if notOnThisCore(error) { noticesAvailability = .notOnThisCore; noticeItems = [] }
            else if SessionModel.isStopRefusal(error) { learnStop() }   // 1.0.17 reads notices during the stop; kept for safety
            else {
                let sentence = report(error)   // said in the sheet, where the owner is looking
                if paired { noticesFailure = sentence }
            }
        }
    }

    /// The paired devices, the PC and the simulated client (`devices`). On an older Core the answer is "not on this
    /// Core yet", asked again only when the Core's version changes.
    func loadDevices() async {
        guard paired else { return }
        if devicesAvailability == .notOnThisCore, devicesCheckedOnCore == metrics?.coreVersion { return }
        do {
            deviceList = try await client.devices()
            devicesAvailability = .ready
        } catch {
            if notOnThisCore(error) {
                devicesAvailability = .notOnThisCore
                devicesCheckedOnCore = metrics?.coreVersion
                deviceList = nil
            } else if SessionModel.isStopRefusal(error) {
                learnStop()   // asked again at the next overview reading
            } else if (error as? ClientFailure) != .unreachable, !SessionModel.isBusy(error) {
                healthNote = report(error)   // busy: asked again at the next overview reading
            }
        }
    }

    /// One sparkline sample per reading; the last 60 are kept (five minutes at the polling pace).
    private func appendHealthSample(_ reading: Metrics) {
        healthHistory.append(HealthSample(cpu: reading.cpuPercent, memory: reading.memory?.usedPercent,
                                          disk: reading.disk?.usedPercent, link: roundTripMs.map(Double.init)))
        if healthHistory.count > SessionModel.healthHistoryLimit {
            healthHistory.removeFirst(healthHistory.count - SessionModel.healthHistoryLimit)
        }
    }

    /// A level from the recorder (about twelve a second during a hold); the last 48 draw the waveform. In hands-free
    /// listening the levels also end the recording: after speech, 1.3 s of quiet sends it; with no speech at all,
    /// 4 s of quiet ends it (the Core then says nothing was heard).
    private func pushMicLevel(_ level: Double) {
        guard recording else { return }
        micLevels.append(level)
        if micLevels.count > 48 { micLevels.removeFirst(micLevels.count - 48) }
        guard handsFree else { return }
        let now = Date()
        if micLevels.count == 1 { lastLoudAt = now }   // the counts start at the first audio, not at the press
        // Speech is what rises well above this recording's own quietest buffer (the room), never below a floor:
        // a soft voice at arm's length still counts, a fan or traffic does not pause (the 30 s limit then sends).
        levelFloor = min(levelFloor ?? level, level)
        let threshold = max(SessionModel.speechLevelMinimum, SessionModel.speechAboveFloor * (levelFloor ?? level))
        if level >= threshold {
            heardSpeech = true
            lastLoudAt = now
            return
        }
        let quiet = now.timeIntervalSince(lastLoudAt)
        if heardSpeech, quiet >= SessionModel.pauseThatSends {
            holdToSpeakEnded()
        } else if !heardSpeech, quiet >= SessionModel.silenceThatGivesUp {
            // Nothing was said: the recording is dropped, not sent (speech recognition turns room noise into words).
            endRecording(saying: "Nothing was heard. Press the button again and speak, or hold the microphone.")
        }
    }

    /// Levels are 0 to 1 (four times the RMS of a buffer). A buffer counts as speech at or above three times the
    /// recording's quietest buffer and never below 0.08.
    static let speechLevelMinimum = 0.08
    static let speechAboveFloor = 3.0
    static let pauseThatSends: TimeInterval = 1.3
    static let silenceThatGivesUp: TimeInterval = 4.0
    /// A press that could not start (the lock, the hello) starts within this time of the press; later it is dropped,
    /// so that an unlock an hour later never starts listening unasked.
    static let handsFreeMaxAge: TimeInterval = 120

    // MARK: the button and links (jarvis://)

    /// jarvis://listen opens the app listening hands-free; jarvis://stop raises the emergency stop. From the lock
    /// screen and Control Center button (the JARVISControls extension), Back Tap or a Shortcut's "Open URL".
    func handle(url: URL) {
        guard url.scheme?.lowercased() == "jarvis" else { return }
        switch url.host?.lowercased() {
        case "listen":
            requestHandsFree()
        case "stop":
            Task { await stopEverything() }   // as "Hey Siri, stop JARVIS": any app or link on this phone may raise the stop; only RESUME on the PC lifts it
        default:
            notice = "This link to JARVIS is not known."
        }
    }

    /// The button's intent, performed in this app by the system after it opened the app (JARVISShared): it posts a
    /// notification when the app is already running, and leaves a time stamp for a cold start. Either way the
    /// request goes through `requestHandsFree`, and starts only when the app is in front, unlocked and said hello.
    private func watchListenRequests() {
        observers.append(NotificationCenter.default.addObserver(forName: OpenJarvisListeningIntent.requestNotification, object: nil, queue: .main) { [weak self] _ in
            Task { @MainActor in self?.pickUpListenRequest() }
        })
    }

    /// A press left by the button's intent (within two minutes), picked up when the app comes to the front.
    func pickUpListenRequest() {
        guard let at = UserDefaults.standard.object(forKey: OpenJarvisListeningIntent.requestKey) as? Date else { return }
        UserDefaults.standard.removeObject(forKey: OpenJarvisListeningIntent.requestKey)
        guard Date().timeIntervalSince(at) <= SessionModel.handsFreeMaxAge else { return }
        requestHandsFree()
    }

    /// The button was pressed: the Ask screen comes to the front and the request is kept until the app can listen.
    /// Listening starts only when the scene is active, the lock is off and the Core's hello has answered (so the
    /// microphone allowance is known), which may be at once or after the unlock; a request older than two minutes
    /// is dropped unstarted.
    func requestHandsFree() {
        askRequested += 1
        guard paired else {
            notice = "This phone is not paired with JARVIS yet."
            return
        }
        pendingHandsFree = true
        pendingHandsFreeAt = Date()
        startPendingHandsFreeIfReady()
    }

    /// The one place hands-free listening starts: called when the request arrives, when the scene becomes active,
    /// after a successful hello and after a passed unlock. The recording ends at a pause after speech, at a tap on
    /// the microphone, or at the 30 s limit; with no speech it is dropped. A question in progress gives way.
    private func startPendingHandsFreeIfReady() {
        guard pendingHandsFree else { return }
        if let at = pendingHandsFreeAt, Date().timeIntervalSince(at) > SessionModel.handsFreeMaxAge {
            pendingHandsFree = false
            pendingHandsFreeAt = nil
            return
        }
        guard inFront, !locked, info != nil else { return }   // waits for the front, the unlock or the hello
        pendingHandsFree = false
        pendingHandsFreeAt = nil
        if busy || recording { interrupt() }
        heardSpeech = false
        levelFloor = nil
        lastLoudAt = Date()
        handsFree = true
        holdToSpeakBegan()
        if !recording { handsFree = false }   // the hold did not start (microphone not allowed, a question held, the stop): the notice says why
    }

    static let healthHistoryLimit = 60

    /// Every 5 seconds while a screen that shows the numbers is open (12 calls a minute of the 120 allowed).
    func startHealthPolling() {
        stopHealthPolling()
        healthTask = Task { [weak self] in
            var round = 0
            while !Task.isCancelled {
                await self?.refreshHealth(overviewToo: round % 6 == 0)
                if round % 2 == 1 { await self?.checkStatus(quiet: true) }   // the ticks and the waiting and notice counts (Core 1.0.17), every 10 s
                round += 1
                try? await Task.sleep(for: .seconds(5))
            }
        }
    }

    func stopHealthPolling() {
        healthTask?.cancel()
        healthTask = nil
    }

    // MARK: a question

    func send() {
        let text = draft.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }
        guard text.unicodeScalars.count <= 12_000 else {
            notice = "That is more than 12,000 characters. Shorten it."
            return
        }
        guard held == nil else {   // the typed words stay in the field: nothing of the owner's is lost
            notice = SessionModel.heldNotice
            return
        }
        draft = ""
        send(text)
    }

    func send(_ text: String) {
        guard paired, !busy, !text.isEmpty, text.unicodeScalars.count <= 12_000 else { return }
        guard held == nil else {   // one held question at most
            notice = SessionModel.heldNotice
            return
        }
        player.stop()
        generation += 1
        let ticket = generation
        busy = true
        notice = nil
        toolName = nil
        resumable = nil
        state = .thinking
        lines.append(ChatLine(isUser: true, text: text))
        lines = Array(lines.suffix(80))
        work = Task { [weak self] in
            guard let self else { return }
            await self.run(text: text, ticket: ticket)
        }
    }

    private func run(text: String, ticket: Int) async {
        let started: RunStarted
        do {
            // R3: only while the switch is on, no older than two minutes, and only to a Core whose hello or status says
            // `location: true`: an older Core refuses a question with an unknown field ("Unknown fields.",
            // wearables-service.py). With no fix the field is left out, never sent as null ("Invalid location.").
            let location = (sendLocation && (info?.takesLocation ?? false)) ? locations.current(maxAge: 120) : nil
            started = try await client.start(text: text, conversation: conversation, location: location)
        } catch {
            guard generation == ticket else { return }
            busy = false
            if (error as? ClientFailure) == .unreachable {
                // The question's bubble comes off the screen: the held box carries the words until they are sent.
                if let last = lines.last, last.isUser, last.text == text { lines.removeLast() }
                hold(.words(text))
                return
            }
            if SessionModel.isBusy(error) {
                // The Core was still making the last reply's voice (busy twice, the retry included): it took nothing,
                // so the words go back into the type box to be sent again, never lost.
                if let last = lines.last, last.isUser, last.text == text { lines.removeLast() }
                if draft.isEmpty { draft = text }
                notice = "JARVIS was still busy with this phone's last request. Your words are back in the type box (TYPE): send them again."
                state = stopped ? .stopped : .idle
                return
            }
            fail(error)
            return
        }
        heldSince = nil   // the Core has the question: a held wait, if this was one, is over
        guard generation == ticket else {
            // Cancelled while the question was on its way: the Core has it by now, so it is told to stop it.
            let id = started.runId
            Task { [client] in try? await client.cancel(runId: id) }
            return
        }
        stopped = false   // the Core takes no question while the emergency stop holds
        runId = started.runId
        await follow(runId: started.runId, after: -1, ticket: ticket)
    }

    private func resume(_ pending: (runId: String, after: Int)) async {
        resumable = nil
        generation += 1
        let ticket = generation
        busy = true
        notice = nil
        state = .thinking
        runId = pending.runId
        await follow(runId: pending.runId, after: pending.after, ticket: ticket)
    }

    /// The events of a question, from the cursor on, until the Core says it is done; then the reply, spoken.
    private func follow(runId id: String, after start: Int, ticket: Int) async {
        var after = start
        var reply: String?
        var deltas = ""
        var failure: String?
        var cancelled = false
        do {
            while !Task.isCancelled {
                let page = try await client.events(runId: id, after: after)
                guard generation == ticket else { return }
                for event in page.events {
                    after = max(after, event.id)
                    switch event.event {
                    case "run.started": state = .thinking
                    case "tool.started":
                        state = .executing
                        toolName = event.data["name"]?.string
                    case "tool.completed", "tool.failed":
                        state = .thinking
                        toolName = nil
                    case "assistant.delta":
                        if let piece = event.data["text"]?.string { deltas += piece }
                    case "assistant.draft":
                        // The whole text so far, replacing the last draft; empty when a tool ran or the answer stopped.
                        let text = event.data["text"]?.string ?? ""
                        writing = text.isEmpty ? nil : text
                    case "assistant.completed":
                        reply = event.data["text"]?.string ?? reply
                        writing = nil
                    case "run.failed":
                        failure = event.data["message"]?.string ?? "The request failed on the PC."
                    case "run.cancelled":
                        cancelled = true
                    case "provider.backup", "provider.offline":
                        if let reason = event.data["reason"]?.string { notice = reason }
                    default:
                        break
                    }
                }
                if page.done { break }
                if !page.events.isEmpty {
                    // Pieces of an answer arrive at once: a short pause keeps the calls few on cellular.
                    try? await Task.sleep(for: .milliseconds(300))
                }
            }
        } catch {
            guard generation == ticket else { return }
            busy = false
            runId = nil
            writing = nil
            if (error as? ClientFailure) == .unreachable {
                resumable = (id, after)
                reached = false
                state = .offline
                notice = "The connection dropped while JARVIS was answering. The answer is picked up when the link is back."
                return
            }
            fail(error)
            return
        }
        guard generation == ticket else { return }
        busy = false
        runId = nil
        toolName = nil
        writing = nil
        if reply == nil, !deltas.isEmpty { reply = deltas }
        if let failure {
            notice = failure
            state = .error
            replyHaptic.notificationOccurred(.error)
            return
        }
        if cancelled {
            // Not asked for by this phone: most likely the emergency stop on the PC. Ask the Core what holds.
            await checkStatus()
            return
        }
        guard let reply, !reply.isEmpty else {
            state = stopped ? .stopped : .idle
            return
        }
        lines.append(ChatLine(isUser: false, text: reply))
        lines = Array(lines.suffix(80))
        replyHaptic.notificationOccurred(.success)   // the reply is here: a short vibration, with or without the voice
        // The Core's status decides the stop, not the reply's words (a reply may only talk about the emergency
        // stop); a tool set to Ask first may now wait, so the count shows with the reply (R2).
        if (info?.tools ?? false) || reply.localizedCaseInsensitiveContains("emergency stop is on") {
            await checkStatus(quiet: true)
        }
        guard generation == ticket else { return }
        if rereadAfterRun {   // an approval applied during this run: its "Approved from ..." line, as the Core keeps it
            rereadAfterRun = false
            await refreshLinesFromCore()
            guard generation == ticket else { return }
        }
        if speakReplies, !locked, info?.allows(.speakers) ?? false, !stopped {   // nothing is read aloud over the lock screen
            await speak(reply, ticket: ticket)
        }
        guard generation == ticket else { return }
        state = stopped ? .stopped : .idle
    }

    /// The reply in JARVIS's voice: the Core makes the sound, the phone plays it.
    private func speak(_ text: String, ticket: Int) async {
        state = .speaking
        do {
            let spoken = try await client.speech(text: text)
            guard generation == ticket, let sound = Data(base64Encoded: spoken.audio), !sound.isEmpty else { return }
            try await player.play(sound)
        } catch {
            guard generation == ticket else { return }
            if SessionModel.isStopRefusal(error) { learnStop() }   // the stop came while the voice was made
            notice = report(error)   // the text is on screen either way
        }
    }

    func interrupt() {
        generation += 1
        writing = nil
        held = nil      // a new conversation, the emergency stop or a forgotten pairing: nothing waits any more
        heldSince = nil
        if busy && runId == nil {
            // The question is on its way to the Core: run() learns the id and sends the cancel itself.
        } else {
            work?.cancel()
        }
        work = nil
        player.stop()
        if recording {
            recorder.cancel()
            recording = false
            handsFree = false
            micLevels = []
        }
        pendingHandsFree = false
        pendingHandsFreeAt = nil
        if let runId {
            let id = runId
            Task { [client] in try? await client.cancel(runId: id) }
        }
        runId = nil
        resumable = nil
        busy = false
        toolName = nil
        if paired, state != .offline { state = stopped ? .stopped : .idle }
    }

    /// The app left the front (a call, a system alert, another app): a recording in progress is dropped, a
    /// question in progress is left to the Core and picked up on return.
    func sceneInactive() {
        inFront = false
        endRecording(saying: nil)
    }

    // MARK: sounds around the app (a call, another app's sound, a headset)

    private func watchAudio() {
        // A call or another app's sound while recording: the recording is dropped and the owner is told. (The
        // reply's sound is the player's own business: paused by iOS and resumed or ended afterwards.)
        observers.append(NotificationCenter.default.addObserver(forName: AVAudioSession.interruptionNotification, object: nil, queue: .main) { [weak self] note in
            let began = (note.userInfo?[AVAudioSessionInterruptionTypeKey] as? UInt) == AVAudioSession.InterruptionType.began.rawValue
            guard began else { return }
            Task { @MainActor in self?.endRecording(saying: "A call or another app interrupted the recording. Hold the microphone again.") }
        })
    }

    private func endRecording(saying message: String?) {
        guard recording else { return }
        recorder.cancel()
        recording = false
        handsFree = false
        micLevels = []
        if let message { notice = message }
        state = stopped ? .stopped : .idle
    }

    // MARK: hold to speak

    func holdToSpeakBegan() {
        guard paired, !busy, !recording else { return }
        guard held == nil else {
            notice = "One question is already held for the Core. DROP it, or wait for the link."
            return
        }
        guard !stopped else {   // the Core takes no recording while the stop holds: no 30 s wait for a refusal
            notice = "JARVIS is stopped. Press RESUME on the PC to continue."
            return
        }
        guard info?.allows(.microphone) ?? false else {
            notice = "The microphone of this phone is not allowed yet. The owner allows it in Settings > Devices on the PC."
            return
        }
        player.stop()
        notice = nil
        recording = true
        recordingSeconds = 0
        micLevels = []
        state = .listening
        holdHaptic.impactOccurred()   // the hold has taken: felt, so the eyes can stay elsewhere
        recorder.start(
            progress: { [weak self] seconds in Task { @MainActor in self?.recordingSeconds = seconds } },
            level: { [weak self] level in Task { @MainActor in self?.pushMicLevel(level) } },
            limitReached: { [weak self] in Task { @MainActor in self?.holdToSpeakEnded() } },
            failed: { [weak self] message in
                Task { @MainActor in
                    guard let self else { return }
                    self.recording = false
                    self.handsFree = false
                    self.micLevels = []
                    self.notice = message
                    self.state = self.stopped ? .stopped : .idle
                }
            })
    }

    func holdToSpeakEnded() {
        guard recording else { return }
        recording = false
        handsFree = false
        micLevels = []   // the waveform goes flat and the orb's glow settles once the hold is over
        let pcm = recorder.stop()
        guard pcm.count >= 3200 else {   // under a tenth of a second: nothing was said
            state = stopped ? .stopped : .idle
            return
        }
        transcribeAndSend(pcm)
    }

    /// The recording goes to the Core's speech recognition, and the words it heard become the question. When the
    /// Core cannot be reached the recording is held and sent when the link is back.
    private func transcribeAndSend(_ pcm: Data) {
        generation += 1
        let ticket = generation
        state = .thinking
        busy = true
        work = Task { [weak self] in
            guard let self else { return }
            do {
                let heard = try await self.client.transcribe(pcm16: pcm)
                guard self.generation == ticket else { return }
                self.busy = false
                self.heldSince = nil   // the recording reached the Core: a held wait, if this was one, is over
                let text = heard.text.trimmingCharacters(in: .whitespacesAndNewlines)
                guard !text.isEmpty else {
                    self.notice = "Nothing was heard. Hold the microphone and speak."
                    self.state = self.stopped ? .stopped : .idle
                    return
                }
                self.send(text)
            } catch {
                guard self.generation == ticket else { return }
                self.busy = false
                if (error as? ClientFailure) == .unreachable {
                    self.hold(.voice(pcm))
                    return
                }
                self.fail(error)
            }
        }
    }

    /// For VoiceOver, which cannot hold a button: one action starts the recording, the next ends and sends it.
    func toggleRecording() {
        if recording { holdToSpeakEnded() } else { holdToSpeakBegan() }
    }

    // MARK: the emergency stop

    /// Any paired device may stop everything; none can resume. RESUME is on the PC.
    func stopEverything() async {
        interrupt()
        do {
            let answer = try await client.stop()
            stopped = answer.stopped
            state = .stopped
            notice = "Emergency stop is on. JARVIS does nothing until RESUME is pressed on the PC."
            replyHaptic.notificationOccurred(.warning)
        } catch {
            fail(error)
        }
    }

    // MARK: the lock (Face ID or the passcode before the screens show)

    /// The app came to the front: locked at every open (init) and after more than a minute in the background, when
    /// the lock is on. Only a stay in the background counts: the control centre, a call banner, the Siri overlay and
    /// the Face ID sheet itself make the scene inactive and active again, and must not lock or prompt (review
    /// finding 1). The prompt itself comes from LockView (on appear and from UNLOCK), never from here.
    func cameToFront() {
        inFront = true
        let hidden = hiddenAt
        hiddenAt = nil
        pickUpListenRequest()   // a button press that opened the app from cold (the lock, if on, comes next)
        if lockEnabled, paired, !locked, let hidden, Date().timeIntervalSince(hidden) >= SessionModel.lockGraceSeconds {
            // A recording in progress (a button press that arrived before the scene was active) must not go on
            // behind the lock screen: it ends here, and a hands-free one starts again after the unlock.
            if recording {
                let resumeAfterUnlock = handsFree
                endRecording(saying: nil)
                if resumeAfterUnlock {
                    pendingHandsFree = true
                    pendingHandsFreeAt = Date()
                }
            }
            locked = true   // RootView shows LockView, whose onAppear asks
        } else if !lockEnabled || !paired {
            locked = false
        }
        startPendingHandsFreeIfReady()
    }

    func leftFront() {
        hiddenAt = Date()
        inFront = false
        pendingHandsFree = false   // a press not started before the phone went away is not started later unasked
        pendingHandsFreeAt = nil
    }

    /// Face ID, or the phone's passcode when Face ID is not set up or does not match. A phone with neither cannot
    /// lock: the switch goes off again and says so.
    func unlock() async {
        guard locked, !unlocking else { return }
        unlocking = true
        defer { unlocking = false }
        let context = LAContext()
        context.localizedCancelTitle = "Not now"
        var unavailable: NSError?
        guard context.canEvaluatePolicy(.deviceOwnerAuthentication, error: &unavailable) else {
            locked = false
            lockEnabled = false
            notice = "This phone has no passcode or Face ID set up, so the JARVIS lock is off."
            return
        }
        let passed = (try? await context.evaluatePolicy(.deviceOwnerAuthentication, localizedReason: "Unlock JARVIS")) ?? false
        if passed {
            locked = false   // MainTabs appears and its first hello picks up a Siri question or a lost answer
            startPendingHandsFreeIfReady()   // the button was pressed over the lock screen
        }
        // Cancelled or not matched: the lock screen stays, with its UNLOCK button and STOP ALL.
    }

    // MARK: Siri

    private func watchSiri() {
        observers.append(NotificationCenter.default.addObserver(forName: .jarvisSiriQuestion, object: nil, queue: .main) { [weak self] _ in
            Task { @MainActor in self?.pickUpSiriQuestion() }
        })
    }

    /// A question Siri took ("Hey Siri, ask JARVIS"): sent as if typed, once the app is in front and unlocked. A
    /// question in progress gives way to it. When the Core cannot be reached it is held like a typed one; one
    /// older than two minutes, or arriving while another question is already held, is dropped and said so.
    func pickUpSiriQuestion() {
        guard let question = AppSettings.siriQuestion else { return }
        if locked { return }                 // sent right after the unlock
        AppSettings.siriQuestion = nil
        guard paired else { return }         // the intent itself says "pair first"; nothing is kept
        let age = AppSettings.siriQuestionAt.map { Date().timeIntervalSince($0) } ?? 0
        guard age < SessionModel.siriQuestionMaxAge else {
            notice = "The question Siri took was not sent: it was more than two minutes ago. Ask again."
            return
        }
        guard held == nil else {
            notice = "The question Siri took was not sent: one question is already held for the Core. DROP it and ask again."
            return
        }
        if busy || recording { interrupt() }
        send(question)
    }

    // MARK: conversations

    func newConversation() {
        interrupt()
        historyPending = false
        rereadAfterRun = false
        conversation = SessionModel.newConversationId(deviceId: AppSettings.deviceId)
        AppSettings.conversation = conversation
        lines = []
        notice = nil
    }

    /// Continue one of this phone's own conversations, as the Core keeps it.
    func open(_ summary: ConversationSummary, history: ConversationHistory) {
        let hadHeld = held != nil
        interrupt()
        historyPending = false
        rereadAfterRun = false
        conversation = summary.id
        AppSettings.conversation = conversation
        lines = history.messages.map { ChatLine(isUser: $0.role == "user", text: $0.content) }.suffix(80).map { $0 }
        notice = hadHeld ? "The held question was dropped when this conversation was opened." : nil
    }

    /// Every conversation of a device starts with the device's own id (the Core refuses any other).
    static func newConversationId(deviceId: String?) -> String {
        let stamp = DateFormatter()
        stamp.dateFormat = "yyyyMMdd-HHmmss"
        stamp.locale = Locale(identifier: "en_US_POSIX")
        return "device-\(deviceId ?? "unpaired")-\(stamp.string(from: Date()))"
    }

    // MARK: failures

    /// A failure outside a question (Chats, Status, the spoken reply): the sentence to show, with a refused key
    /// acted on the same way as everywhere else.
    @discardableResult
    func report(_ error: Error) -> String {
        let failure = error as? ClientFailure
        if let failure, failure.needsPairing { fail(failure) }
        if failure == .unreachable { reached = false }
        return failure?.errorDescription ?? "Something went wrong on the phone."
    }

    private func fail(_ error: Error) {
        let failure = error as? ClientFailure
        notice = failure?.errorDescription ?? "Something went wrong on the phone."
        if let failure, failure.needsPairing {
            // Revoked on the PC, or the pairing is gone: the phone must pair again. The address is kept.
            Keychain.delete()
            client.credential = nil
            stopHealthPolling()
            paired = false
            locked = false
            historyPending = false
            clearCoreData()
            state = .offline
            return
        }
        if failure == .unreachable || failure == .notPaired {
            reached = false
            state = .offline
            return
        }
        if SessionModel.isStopRefusal(error) {
            stopped = true
            state = .stopped
            return
        }
        state = .error
    }

    /// The Core's refusal while the emergency stop holds: its stop sentence ("Emergency stop is on. ..."), which the
    /// question routes and the 1.0.17 approval routes send as HTTP 400 (a 403 carrying it is read the same way).
    /// While the stop holds the Core refuses start (but the stop words), transcribe, speech, approvals, approve,
    /// reject and announce; the reads, hello, status, events, cancel and bye answer as usual (MAC-BRIEF-20261010.md).
    static func isStopRefusal(_ error: Error) -> Bool {
        switch error as? ClientFailure {
        case .rejected(let text)?, .notAllowed(let text)?: return text.localizedCaseInsensitiveContains("emergency stop")
        default: return false
        }
    }

    /// The Core's "Wearable service busy." (another request of this phone held its turn; CoreClient has already sent
    /// the request once more): nothing was done on the PC.
    static func isBusy(_ error: Error) -> Bool {
        if case .rejected(let sentence)? = error as? ClientFailure { return sentence == ClientFailure.busySentence }
        return false
    }

    /// A route other than a question was refused because the stop holds: the screens show the stop at once instead
    /// of at the next status reading, and nothing waits for approval any more (the stop drops every waiting item).
    private func learnStop() {
        stopped = true
        approvals = []
        if !busy && !recording && state != .speaking { state = .stopped }
    }
}
