import Foundation

// What the Core says and expects on its device routes (docs/DEVICES.md section 3, docs/PHONE-CORE-1.0.16.md
// sections 3 and 6). The wire names are the Core's; nothing here is a second source of truth.

/// Presentation states, as wearables/states.py names them. The Core never sends a state word to a device: the app
/// derives these from the events of a question and from what it is doing itself (recording, playing).
enum JarvisState: String, CaseIterable, Sendable {
    case offline = "OFFLINE", idle = "IDLE", listening = "LISTENING", thinking = "THINKING"
    case executing = "EXECUTING", speaking = "SPEAKING", stopped = "STOPPED", error = "ERROR"
}

/// What this phone declares to the Core. The Core knows microphone, camera, speakers and display; since round 6 the
/// phone declares all four ("Look at this" sends a picture). Declaring is not allowing: the owner ticks each one for
/// this phone on the PC (Settings > Devices), and a picture is refused until the camera is ticked.
enum Capability: String, Codable, CaseIterable, Sendable {
    case microphone, camera, speakers, display
    static let declared: [Capability] = [.microphone, .camera, .speakers, .display]
}

/// The answer to `pair`: the device's identity, given once.
struct Paired: Decodable, Sendable {
    let deviceId: String
    let key: String
    let credential: String
    let name: String
    let kind: String
    let allowed: [String]
    let writes: Bool
    enum CodingKeys: String, CodingKey { case deviceId = "device_id", key, credential, name, kind, allowed, writes }
}

/// The answer to `hello` and `status`. The five fields of Core 1.0.17 (docs/MAC-REQUESTS-20261007.md and the PC's
/// brief of 2026-10-10) are optional: an older Core leaves them out, and a missing field reads as false or zero.
struct DeviceInfo: Decodable, Sendable {
    let deviceId: String
    let name: String
    let kind: String
    let declared: [String]
    let allowed: [String]
    /// True when the owner ticked "May save memories and tasks" or "May use this PC's tools" (the tools include saving).
    let writes: Bool
    let stopped: Bool
    let protocolVersion: Int
    let scope: String
    let toolsField: Bool?
    let approveField: Bool?
    let waitingField: Int?
    let noticesField: Int?
    let locationField: Bool?
    enum CodingKeys: String, CodingKey {
        case deviceId = "device_id", name, kind, declared, allowed, writes, stopped, protocolVersion = "protocol", scope
        case toolsField = "tools", approveField = "approve", waitingField = "waiting", noticesField = "notices"
        case locationField = "location"
    }
    func allows(_ capability: Capability) -> Bool { allowed.contains(capability.rawValue) }
    /// Whether this Core takes `start.location`: only when it says `location: true`. An older Core refuses the whole
    /// question with HTTP 400 "Unknown fields.", so the phone's position is never sent to it.
    var takesLocation: Bool { locationField == true }
    /// The owner's tick "May use this PC's tools" for this device.
    var tools: Bool { toolsField ?? false }
    /// The owner's tick "May approve for JARVIS" for this device.
    var approve: Bool { approveField ?? false }
    /// Approvals waiting for an answer (counted only when `approve` is on).
    var waiting: Int { waitingField ?? 0 }
    /// Notices this device has not read yet.
    var notices: Int { noticesField ?? 0 }
    /// Whether this Core sends the 1.0.17 approval fields (feature presence is read from the fields, not a version).
    var servesApprovals: Bool { approveField != nil }
    /// Whether this Core sends the notices count.
    var servesNotices: Bool { noticesField != nil }
}

// MARK: Core 1.0.17 routes (docs/MAC-REQUESTS-20261007.md section 2)

/// One item waiting for the owner's word (`approvals`).
struct ApprovalItem: Decodable, Identifiable, Sendable, Equatable {
    let id: String
    let kind: String          // tool, memory, self_change, draft
    let tool: String?
    let label: String
    let detail: String
    let created: Double
    let expires: Double
    let runId: String?
    let conversation: String?
    let device: String
    let deviceName: String
    enum CodingKeys: String, CodingKey {
        case id, kind, tool, label, detail, created, expires, runId = "run_id", conversation, device, deviceName = "device_name"
    }
}

struct ApprovalList: Decodable, Sendable { let items: [ApprovalItem] }

/// What came of an answer the owner gave (a receipt shown under the list).
struct ApprovalOutcome: Identifiable, Equatable, Sendable {
    enum Kind: Equatable, Sendable { case applied, denied, failed, error }
    let id: String
    let label: String
    let sentence: String
    let kind: Kind

    static func kind(of status: String) -> Kind {
        switch status {
        case "applied": return .applied
        case "denied": return .denied
        case "failed", "expired", "unknown": return .failed
        default: return .failed
        }
    }
}

/// The answer to `approve` or `reject`: applied (with a receipt), failed, denied, expired or unknown.
struct ApprovalAnswer: Decodable, Sendable {
    let status: String
    let result: String?
}

/// One line the Core has for this device (`notices`): a nudge, an announcement, a waiting approval, a system note.
struct NoticeItem: Decodable, Identifiable, Sendable, Equatable {
    let id: String
    let kind: String
    let text: String
    let created: Double
}

struct NoticeList: Decodable, Sendable {
    let items: [NoticeItem]
    let unread: Int
}

/// The answer to `announce`: whether the PC took it and whether it could speak it.
struct Announced: Decodable, Sendable {
    let announced: Bool
    let spoken: Bool
}

/// The paired devices as the Core lists them (`devices`), the PC itself, and the simulated test client.
struct DeviceList: Decodable, Sendable {
    struct Device: Decodable, Identifiable, Sendable {
        let id: String
        let name: String
        let kind: String
        let online: Bool
        let lastSeen: Double?
        let allowed: [String]
        let writes: Bool
        let tools: Bool
        let approve: Bool
        let thisDevice: Bool
        enum CodingKeys: String, CodingKey {
            case id, name, kind, online, lastSeen = "last_seen", allowed, writes, tools, approve, thisDevice = "this_device"
        }
    }
    struct PC: Decodable, Sendable {
        let name: String
        let coreVersion: String
        let online: Bool
        enum CodingKeys: String, CodingKey { case name, coreVersion = "core_version", online }
    }
    struct Simulated: Decodable, Sendable {
        let name: String
        let kind: String
        let online: Bool?   // new in 1.0.18's devices op; missing reads as not known
    }
    let devices: [Device]
    let pc: PC
    let simulated: [Simulated]
}

/// A calendar item of the owner's next 24 hours (`overview.calendar`, when the owner has signed in to Google on the PC).
struct CalendarItem: Decodable, Sendable, Equatable {
    let title: String
    let start: Double
    let end: Double
    let allDay: Bool
    let location: String?
    enum CodingKeys: String, CodingKey { case title, start, end, allDay = "all_day", location }
}

/// The phone's position sent with a question while the owner's switch is on (`start.location`): the Core gives it
/// to the model for that answer and stores nothing unless the owner's words ask it to.
struct QuestionLocation: Sendable, Equatable {
    let lat: Double
    let lon: Double
    let accuracyM: Double?
    let label: String?

    var body: [String: Any] {
        var fields: [String: Any] = ["lat": lat, "lon": lon]
        if let accuracyM { fields["accuracy_m"] = accuracyM }
        if let label { fields["label"] = String(label.prefix(80)) }
        return fields
    }
}

struct RunStarted: Decodable, Sendable {
    let runId: String
    enum CodingKeys: String, CodingKey { case runId = "run_id" }
}

/// One event of a question, as the Core records it: {id, run_id, event, data}.
struct RunEvent: Decodable, Sendable {
    let id: Int
    let runId: String
    let event: String
    let data: JSONValue
    enum CodingKeys: String, CodingKey { case id, runId = "run_id", event, data }
}

struct RunEvents: Decodable, Sendable {
    let done: Bool
    let events: [RunEvent]
}

struct Transcription: Decodable, Sendable {
    let text: String
    let latencyMs: Int?
    enum CodingKeys: String, CodingKey { case text, latencyMs = "latency_ms" }
}

struct Spoken: Decodable, Sendable {
    let audio: String   // base64 of the sound, MP3 or WAV
    let mime: String
    let ttsMs: Int?
    enum CodingKeys: String, CodingKey { case audio, mime, ttsMs = "tts_ms" }
}

struct Stopped: Decodable, Sendable { let stopped: Bool }
struct Cancelled: Decodable, Sendable { let cancelled: Bool }
struct Disconnected: Decodable, Sendable { let disconnected: Bool }

/// One of this phone's conversations, from `conversations`.
struct ConversationSummary: Decodable, Identifiable, Sendable {
    let id: String
    let created: Double
    let updated: Double
    let messages: Int
    let title: String?
    let last: String?
}

struct ConversationList: Decodable, Sendable { let conversations: [ConversationSummary] }

struct StoredMessage: Decodable, Identifiable, Sendable {
    let id: Int
    let role: String
    let content: String
    let created: Double
}

struct ConversationHistory: Decodable, Sendable {
    let conversation: String
    let messages: [StoredMessage]
}

/// The PC's health as the dashboard has it (`metrics`): nothing is measured that the PC does not measure.
struct Metrics: Decodable, Sendable {
    struct Share: Decodable, Sendable {
        let usedPercent: Double?
        enum CodingKeys: String, CodingKey { case usedPercent = "used_percent" }
    }
    let sampledAt: Double
    let cpuPercent: Double?
    let memory: Share?
    let disk: Share?
    let coreUptimeSeconds: Int?
    let lastResponseMs: Double?
    let coreVersion: String
    let aiReady: Bool
    let stopped: Bool
    enum CodingKeys: String, CodingKey {
        case sampledAt = "sampled_at", cpuPercent = "cpu_percent", memory, disk, coreUptimeSeconds = "core_uptime_seconds"
        case lastResponseMs = "last_response_ms", coreVersion = "core_version", aiReady = "ai_ready", stopped
    }
}

/// A question made while the Core could not be reached, kept on the phone until the link is back (hold-and-send,
/// 2026-10-07): the typed words, or the recording of a hold that could not be transcribed yet. The phone never
/// answers it; it only stops losing it. Dropped after `SessionModel.heldQuestionMaxAge`, on a new conversation,
/// on the emergency stop, or by the owner's DROP.
enum HeldQuestion: Equatable, Sendable {
    case words(String)
    case voice(Data)

    /// What the Ask screen shows while it waits.
    var shown: String {
        switch self {
        case .words(let text): return text
        case .voice: return "your recording"
        }
    }
}

/// One reading of the PC's health as this phone saw it, for the Overview's sparklines: the Core's CPU, memory and
/// storage shares and this phone's own round trip. The screen's copy only; nothing is kept past the app's run.
struct HealthSample: Sendable {
    let cpu: Double?
    let memory: Double?
    let disk: Double?
    let link: Double?
}

/// `overview`: open tasks, projects with their open tasks, the reminders due within a day.
struct Overview: Decodable, Sendable {
    struct Project: Decodable, Identifiable, Sendable {
        let id: String
        let name: String
        let openTasks: Int
        enum CodingKeys: String, CodingKey { case id, name, openTasks = "open_tasks" }
    }
    struct Reminder: Decodable, Sendable {
        let title: String
        let due: Double
        let fired: Bool
    }
    let tasksOpen: Int
    let projects: [Project]
    let reminders: [Reminder]
    let conversations: Int
    // Core 1.0.17: the owner's Google calendar and inbox when signed in on the PC; an older Core leaves them out.
    let calendarConnected: Bool?
    let calendar: [CalendarItem]?
    let mailUnread: Int?
    enum CodingKeys: String, CodingKey {
        case tasksOpen = "tasks_open", projects, reminders, conversations
        case calendarConnected = "calendar_connected", calendar, mailUnread = "mail_unread"
    }
}

/// A line of the conversation as shown on the Ask screen (the Core keeps the record; this is the screen's copy).
struct ChatLine: Identifiable, Equatable, Sendable {
    let id = UUID()
    let isUser: Bool
    let text: String
    /// A small copy of the picture a question carried ("Look at this", round 6), on this screen only: the Core keeps
    /// the picture with the question, and lines read back from it have none.
    var photo: Data? = nil
}

/// A JSON value of any shape, for event data the app reads a field or two from.
enum JSONValue: Decodable, Sendable, Equatable {
    case string(String), number(Double), bool(Bool), null, array([JSONValue]), object([String: JSONValue])

    init(from decoder: Decoder) throws {
        let c = try decoder.singleValueContainer()
        if c.decodeNil() { self = .null; return }
        if let b = try? c.decode(Bool.self) { self = .bool(b); return }
        if let n = try? c.decode(Double.self) { self = .number(n); return }
        if let s = try? c.decode(String.self) { self = .string(s); return }
        if let a = try? c.decode([JSONValue].self) { self = .array(a); return }
        if let o = try? c.decode([String: JSONValue].self) { self = .object(o); return }
        throw DecodingError.dataCorruptedError(in: c, debugDescription: "Unsupported JSON value")
    }

    subscript(key: String) -> JSONValue? {
        if case .object(let o) = self { return o[key] }
        return nil
    }
    var string: String? { if case .string(let s) = self { return s } else { return nil } }
}
