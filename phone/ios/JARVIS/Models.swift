import Foundation

// What the Core says and expects on its device routes (docs/DEVICES.md section 3, docs/PHONE-CORE-1.0.16.md
// sections 3 and 6). The wire names are the Core's; nothing here is a second source of truth.

/// Presentation states, as wearables/states.py names them. The Core never sends a state word to a device: the app
/// derives these from the events of a question and from what it is doing itself (recording, playing).
enum JarvisState: String, CaseIterable, Sendable {
    case offline = "OFFLINE", idle = "IDLE", listening = "LISTENING", thinking = "THINKING"
    case executing = "EXECUTING", speaking = "SPEAKING", stopped = "STOPPED", error = "ERROR"
}

/// What this phone declares to the Core. The Core knows microphone, camera, speakers and display; the phone
/// declares the three it uses in version 1 (the camera is version 2).
enum Capability: String, Codable, CaseIterable, Sendable {
    case microphone, camera, speakers, display
    static let declared: [Capability] = [.microphone, .speakers, .display]
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

/// The answer to `hello` and `status`.
struct DeviceInfo: Decodable, Sendable {
    let deviceId: String
    let name: String
    let kind: String
    let declared: [String]
    let allowed: [String]
    let writes: Bool
    let stopped: Bool
    let protocolVersion: Int
    let scope: String
    enum CodingKeys: String, CodingKey {
        case deviceId = "device_id", name, kind, declared, allowed, writes, stopped, protocolVersion = "protocol", scope
    }
    func allows(_ capability: Capability) -> Bool { allowed.contains(capability.rawValue) }
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
    enum CodingKeys: String, CodingKey { case tasksOpen = "tasks_open", projects, reminders, conversations }
}

/// A line of the conversation as shown on the Ask screen (the Core keeps the record; this is the screen's copy).
struct ChatLine: Identifiable, Equatable, Sendable {
    let id = UUID()
    let isUser: Bool
    let text: String
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
