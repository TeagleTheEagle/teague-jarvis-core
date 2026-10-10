import Foundation

// One question to the Core from outside the app's screens (round 6): Siri answering in place ("Hey Siri, ask
// JARVIS", item 13) and Share to JARVIS (item 12). Sent with `start` and followed with `events` as the Ask screen
// follows a question, until the reply, a failure or the time given. When the time runs out the question goes on at
// the Core, which keeps the reply in the conversation (Chats, and the Ask screen when that conversation is open).
// Nothing is answered on the phone: every word of a reply is the Core's.

enum OneQuestion {
    enum Outcome: Equatable, Sendable {
        case reply(String)        // the finished reply, as the Core wrote it
        case failed(String)       // the Core's sentence for a failed question
        case cancelled            // cancelled on the PC: most likely the emergency stop
        case stillWorking         // the time ran out; the Core goes on and keeps the reply
        case linkLost             // the link dropped after the Core had the question; the Core keeps the reply
        case noReply              // done, and nothing was said
    }

    /// Sends the question and follows it, all within `waitAtMost` from the call: every request waits only for the
    /// time left (the Core holds an `events` call up to 10 s when there is no news). A failure of `start` is thrown
    /// as it comes (ClientFailure: not reached, the stop, busy, a refused key); once the Core has the question only a
    /// refused key is thrown. `writing` gets the reply as it is being written (Core 1.0.17's `assistant.draft`: the
    /// whole text so far, nil when it goes away); `tool` the tool at work (nil when none).
    @MainActor
    static func ask(_ client: HTTPCoreClient, text: String, conversation: String, image: String? = nil,
                    location: QuestionLocation? = nil, waitAtMost: TimeInterval,
                    writing: ((String?) -> Void)? = nil, tool: ((String?) -> Void)? = nil) async throws -> Outcome {
        let deadline = Date().addingTimeInterval(waitAtMost)
        func left() -> TimeInterval { deadline.timeIntervalSinceNow }
        let started = try await client.start(text: text, conversation: conversation, location: location, image: image,
                                             timeout: max(3, min(image == nil ? 30 : 60, left())))
        var after = -1
        var reply: String?
        var deltas = ""
        var failure: String?
        var cancelled = false
        while true {
            guard left() > 1 else { return .stillWorking }
            let page: RunEvents
            do {
                page = try await client.events(runId: started.runId, after: after, timeout: min(25, left()))
            } catch {
                let reason = error as? ClientFailure
                if let reason, reason.needsPairing { throw reason }
                // A request cut at the end of the time is the time running out, not the link dropping.
                if reason == .unreachable { return left() <= 1.5 ? .stillWorking : .linkLost }
                return .failed(reason?.errorDescription ?? "The answer could not be read from the PC.")
            }
            for event in page.events {
                after = max(after, event.id)
                switch event.event {
                case "tool.started": tool?(event.data["name"]?.string)
                case "tool.completed", "tool.failed": tool?(nil)
                case "assistant.delta":
                    if let piece = event.data["text"]?.string { deltas += piece }
                case "assistant.draft":
                    let text = event.data["text"]?.string ?? ""
                    writing?(text.isEmpty ? nil : text)
                case "assistant.completed":
                    reply = event.data["text"]?.string ?? reply
                    writing?(nil)
                case "run.failed":
                    failure = event.data["message"]?.string ?? "The request failed on the PC."
                case "run.cancelled":
                    cancelled = true
                default:
                    break
                }
            }
            if page.done {
                if let failure { return .failed(failure) }
                if cancelled { return .cancelled }
                let said = reply ?? (deltas.isEmpty ? nil : deltas)
                guard let said, !said.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return .noReply }
                return .reply(said)
            }
            if Task.isCancelled { return .stillWorking }
            if !page.events.isEmpty, left() > 1.5 { try? await Task.sleep(for: .milliseconds(300)) }   // a few calls, not many
        }
    }
}

/// A reply as plain words, for Siri to show and say: the Markdown marks the PC's window draws (bold, italics, code
/// ticks, links, headings, bullets, code fences) taken out, the words kept as the Core wrote them.
enum PlainWords {
    static func from(_ reply: String) -> String {
        let lines = reply.components(separatedBy: "\n").compactMap { line -> String? in
            if line.trimmingCharacters(in: .whitespaces).hasPrefix("```") { return nil }   // a code fence
            var kept = line.replacingOccurrences(of: #"^\s{0,3}#{1,6}\s+"#, with: "", options: .regularExpression)
            kept = kept.replacingOccurrences(of: #"^(\s*)[-*+]\s+"#, with: "$1", options: .regularExpression)
            return kept
        }
        let joined = lines.joined(separator: "\n")
        let inline = AttributedString.MarkdownParsingOptions(interpretedSyntax: .inlineOnlyPreservingWhitespace)
        if let parsed = try? AttributedString(markdown: joined, options: inline) {
            return String(parsed.characters).trimmingCharacters(in: .whitespacesAndNewlines)
        }
        return joined.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    /// At most about `limit` characters for Siri to say, cut after the last full sentence before the limit (or at a
    /// word when there is none); `cut` says whether anything was left out.
    static func short(_ text: String, limit: Int) -> (text: String, cut: Bool) {
        guard text.count > limit else { return (text, false) }
        let head = String(text.prefix(limit))
        if let end = head.range(of: #"[.!?]\s"#, options: [.regularExpression, .backwards]),
           head.distance(from: head.startIndex, to: end.lowerBound) > limit / 3 {
            return (String(head[..<end.upperBound]).trimmingCharacters(in: .whitespacesAndNewlines), true)
        }
        if let space = head.lastIndex(of: " ") { return (String(head[..<space]) + "…", true) }
        return (head + "…", true)
    }
}

/// Conversation ids. Every conversation of a device starts with the device's own id (the Core refuses any other)
/// and holds only letters, digits, "-" and "_", 80 at most.
enum ConversationIds {
    /// With the milliseconds since round 6: the app, Siri and Share to JARVIS each start conversations, and two in
    /// the same second must not become one.
    static func new(deviceId: String?) -> String {
        let stamp = DateFormatter()
        stamp.dateFormat = "yyyyMMdd-HHmmss-SSS"
        stamp.locale = Locale(identifier: "en_US_POSIX")
        return "device-\(deviceId ?? "unpaired")-\(stamp.string(from: Date()))"
    }
}
