import Foundation

/// Why a request to the Core did not give an answer. The Core's own sentences are shown as they are
/// (docs/DEVICES.md: a device is told a few fixed sentences and nothing else).
enum ClientFailure: Error, LocalizedError, Equatable {
    case notPaired
    case unreachable
    case invalidAddress
    case refusedKey(String)          // 401: pair again
    case notAllowed(String)          // 403: a capability the owner has not ticked, or a refused request
    case tooManyAttempts(String)     // 429: this caller is locked out for a while
    case rejected(String)            // 400: the Core's sentence
    case unavailable(String)         // 503, or an answer that is not JSON
    case tooLarge

    var errorDescription: String? {
        switch self {
        case .notPaired: return "This phone is not paired with JARVIS yet."
        case .unreachable: return "JARVIS cannot be reached. Is Tailscale on, on both the PC and this phone, and the Private network switch on in Settings > Devices?"
        case .invalidAddress: return "Give the PC's Tailscale name or address, and a port between 1 and 65535."
        case .refusedKey(let text), .notAllowed(let text), .tooManyAttempts(let text), .rejected(let text), .unavailable(let text):
            return text
        case .tooLarge: return "That request is too large to send."
        }
    }

    /// The Core's answer when another request of this phone holds its turn for more than two seconds.
    static let busySentence = "Wearable service busy."

    /// A refused key means the owner revoked this phone (or the pairing was lost): pair again.
    var needsPairing: Bool { if case .refusedKey = self { return true } else { return false } }

    /// An older Core answers a 1.0.17 op with 400 "Operation unavailable.": not on this Core yet, nothing invented
    /// (docs/MAC-REQUESTS-20261007.md section 0).
    var notOnThisCore: Bool {
        if case .rejected(let text) = self { return text == "Operation unavailable." }
        return false
    }
}

/// Where the Core is: the PC's Tailscale name (full or short) or address, and the door's port (8790 by default).
struct CoreAddress: Equatable, Codable, Sendable {
    var host: String
    var port: Int

    static let defaultPort = 8790

    /// Plain HTTP inside the Tailscale tunnel (decision D1 of the phone plan).
    var baseURL: URL? {
        let trimmed = host.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        guard !trimmed.isEmpty, (1...65535).contains(port),
              trimmed.range(of: "^[a-z0-9.-]+$", options: .regularExpression) != nil else { return nil }
        return URL(string: "http://\(trimmed):\(port)")
    }
}

/// The Core's device routes: POST /api/device/<op>, JSON in and out, the device's key in X-Jarvis-Device.
@MainActor
protocol CoreClient: AnyObject {
    func pair(address: CoreAddress, code: String, capabilities: [Capability]) async throws -> Paired
    func hello(capabilities: [Capability]) async throws -> DeviceInfo
    func status() async throws -> DeviceInfo
    func start(text: String, conversation: String, location: QuestionLocation?) async throws -> RunStarted
    func events(runId: String, after: Int) async throws -> RunEvents
    func cancel(runId: String) async throws
    func transcribe(pcm16: Data) async throws -> Transcription
    func speech(text: String) async throws -> Spoken
    func stop() async throws -> Stopped
    func bye() async throws
    func conversations() async throws -> [ConversationSummary]
    func history(conversation: String, limit: Int) async throws -> ConversationHistory
    func metrics() async throws -> Metrics
    func overview() async throws -> Overview
    // Core 1.0.17 (docs/MAC-REQUESTS-20261007.md section 2)
    func approvals() async throws -> [ApprovalItem]
    func approve(id: String) async throws -> ApprovalAnswer
    func reject(id: String) async throws -> ApprovalAnswer
    func notices(after: Double?) async throws -> NoticeList
    func announce(sender: String, text: String, kind: String) async throws -> Announced
    func devices() async throws -> DeviceList
}

/// The real client. One Core, one key; every request names the door it goes through (the URL's host and port,
/// which URLSession sends as the Host header). Bodies are bounded JSON (the door accepts up to 3 MB).
@MainActor
final class HTTPCoreClient: CoreClient {
    var address: CoreAddress?
    var credential: String?
    private let session: URLSession

    init(address: CoreAddress?, credential: String?) {
        self.address = address
        self.credential = credential
        let config = URLSessionConfiguration.ephemeral
        config.waitsForConnectivity = false
        config.timeoutIntervalForRequest = 20
        config.timeoutIntervalForResource = 180
        config.httpCookieStorage = nil
        config.urlCache = nil
        session = URLSession(configuration: config)
    }

    // MARK: the routes

    func pair(address: CoreAddress, code: String, capabilities: [Capability]) async throws -> Paired {
        let body: [String: Any] = ["code": code, "capabilities": capabilities.map(\.rawValue)]
        return try await post("pair", body, address: address, credential: nil, timeout: 20)
    }

    func hello(capabilities: [Capability]) async throws -> DeviceInfo {
        try await post("hello", ["capabilities": capabilities.map(\.rawValue)], timeout: 15)
    }

    func status() async throws -> DeviceInfo { try await post("status", [:], timeout: 15) }

    func start(text: String, conversation: String, location: QuestionLocation?) async throws -> RunStarted {
        var body: [String: Any] = ["text": text, "conversation": conversation]
        if let location { body["location"] = location.body }   // only while the owner's switch is on
        return try await post("start", body, timeout: 30)
    }

    func events(runId: String, after: Int) async throws -> RunEvents {
        // The Core waits up to ten seconds for something new: the phone asks a few times, not every tenth of a second.
        try await post("events", ["run_id": runId, "after": after], timeout: 25)
    }

    func cancel(runId: String) async throws {
        let _: Cancelled = try await post("cancel", ["run_id": runId], timeout: 15)
    }

    func transcribe(pcm16: Data) async throws -> Transcription {
        // The Core may wait up to two minutes for its speech model to load the first time.
        try await post("transcribe", ["data": pcm16.base64EncodedString()], timeout: 130)
    }

    func speech(text: String) async throws -> Spoken {
        // The Core counts characters as code points: so does this.
        try await post("speech", ["text": String(text.unicodeScalars.prefix(12_000))], timeout: 60)
    }

    func stop() async throws -> Stopped { try await post("stop", [:], timeout: 15) }

    func bye() async throws { let _: Disconnected = try await post("bye", [:], timeout: 10) }

    func conversations() async throws -> [ConversationSummary] {
        let list: ConversationList = try await post("conversations", [:], timeout: 15)
        return list.conversations
    }

    func history(conversation: String, limit: Int) async throws -> ConversationHistory {
        try await post("history", ["conversation": conversation, "limit": max(1, min(100, limit))], timeout: 15)
    }

    func metrics() async throws -> Metrics { try await post("metrics", [:], timeout: 15) }

    func overview() async throws -> Overview { try await post("overview", [:], timeout: 15) }

    // MARK: Core 1.0.17

    func approvals() async throws -> [ApprovalItem] {
        let list: ApprovalList = try await post("approvals", [:], timeout: 15)
        return list.items
    }

    func approve(id: String) async throws -> ApprovalAnswer { try await post("approve", ["id": id], timeout: 60) }

    func reject(id: String) async throws -> ApprovalAnswer { try await post("reject", ["id": id], timeout: 15) }

    func notices(after: Double?) async throws -> NoticeList {
        var body: [String: Any] = [:]
        if let after { body["after"] = after }
        return try await post("notices", body, timeout: 15)
    }

    func announce(sender: String, text: String, kind: String) async throws -> Announced {
        // The Core counts characters as code points, as for speech; a cut may leave a space at the end, trimmed.
        let who = String(String.UnicodeScalarView(sender.unicodeScalars.prefix(80))).trimmingCharacters(in: .whitespaces)
        let what = String(String.UnicodeScalarView(text.unicodeScalars.prefix(400))).trimmingCharacters(in: .whitespaces)
        return try await post("announce", ["sender": who, "text": what, "kind": kind], timeout: 30)
    }

    func devices() async throws -> DeviceList { try await post("devices", [:], timeout: 15) }

    // MARK: one request

    private func post<T: Decodable>(_ op: String, _ body: [String: Any], timeout: TimeInterval) async throws -> T {
        guard let credential, !credential.isEmpty else { throw ClientFailure.notPaired }
        guard let address else { throw ClientFailure.notPaired }
        return try await post(op, body, address: address, credential: credential, timeout: timeout)
    }

    /// One request, sent again once when the Core says another request of this phone held its turn ("Wearable
    /// service busy.", MAC-BRIEF-20261010.md section 2, item 10): the Core refused it before doing anything.
    private func post<T: Decodable>(_ op: String, _ body: [String: Any], address: CoreAddress, credential: String?,
                                    timeout: TimeInterval) async throws -> T {
        do {
            return try await postOnce(op, body, address: address, credential: credential, timeout: timeout)
        } catch ClientFailure.rejected(let sentence) where sentence == ClientFailure.busySentence {
            try? await Task.sleep(for: .milliseconds(700))
            return try await postOnce(op, body, address: address, credential: credential, timeout: timeout)
        }
    }

    private func postOnce<T: Decodable>(_ op: String, _ body: [String: Any], address: CoreAddress, credential: String?,
                                        timeout: TimeInterval) async throws -> T {
        guard let base = address.baseURL else { throw ClientFailure.invalidAddress }
        guard JSONSerialization.isValidJSONObject(body), let data = try? JSONSerialization.data(withJSONObject: body) else {
            throw ClientFailure.rejected("The request could not be written.")
        }
        guard data.count <= 3 * 1024 * 1024 else { throw ClientFailure.tooLarge }
        var request = URLRequest(url: base.appendingPathComponent("api/device/\(op)"))
        request.httpMethod = "POST"
        request.timeoutInterval = timeout
        request.httpBody = data
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.setValue("JARVIS-iPhone/\(AppInfo.version)", forHTTPHeaderField: "User-Agent")
        if let credential { request.setValue(credential, forHTTPHeaderField: "X-Jarvis-Device") }
        let (answer, response): (Data, URLResponse)
        do {
            (answer, response) = try await session.data(for: request)
        } catch {
            throw ClientFailure.unreachable
        }
        guard let http = response as? HTTPURLResponse else { throw ClientFailure.unreachable }
        if http.statusCode == 200 {
            do { return try JSONDecoder().decode(T.self, from: answer) }
            catch { throw ClientFailure.unavailable("JARVIS answered in a form this app does not know.") }
        }
        let sentence = (try? JSONDecoder().decode(ErrorAnswer.self, from: answer))?.error
        switch http.statusCode {
        case 401: throw ClientFailure.refusedKey(sentence ?? "Device key invalid or revoked. Pair this device again on the PC.")
        case 403: throw ClientFailure.notAllowed(sentence ?? "Not allowed.")
        case 429: throw ClientFailure.tooManyAttempts(sentence ?? "Too many attempts from this device. Wait fifteen minutes.")
        case 400: throw ClientFailure.rejected(sentence ?? "Invalid, busy, expired or unavailable device request.")
        case 404: throw ClientFailure.unavailable("That address is not JARVIS's private-network door.")
        default: throw ClientFailure.unavailable(sentence ?? "JARVIS service unavailable.")
        }
    }

    private struct ErrorAnswer: Decodable { let error: String }
}
