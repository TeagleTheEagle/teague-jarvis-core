import SwiftUI
import WidgetKit

// The Home Screen widget (round 6, item 11, the owner's "build round 6 ... 11 and 12", 2026-10-10): whether JARVIS is
// online or stopped, and how many approvals and notices wait for this phone, with the time of that reading. It asks
// the Core itself (`status`, with this phone's key from the shared Keychain group) each time iPhone draws it: about
// every 15 minutes, and when the app sees the stop or a count change. A tap opens the app; on the medium size a tap
// on a count opens that list. Nothing is invented: when the Core cannot be reached it says Offline, with no counts.

struct JarvisStatusWidget: Widget {
    var body: some WidgetConfiguration {
        StaticConfiguration(kind: WidgetKinds.status, provider: StatusProvider()) { entry in
            StatusWidgetView(entry: entry)
                .containerBackground(for: .widget) { WidgetGround() }
        }
        .configurationDisplayName("JARVIS")
        .description("Whether JARVIS is online or stopped, and the approvals and notices waiting for you.")
        .supportedFamilies([.systemSmall, .systemMedium])
    }
}

/// One reading of the Core, as the widget shows it.
struct StatusEntry: TimelineEntry {
    enum Reading: Equatable {
        case gallery                     // the widget gallery's preview: words only, no numbers
        case openApp                     // no Core address shared yet: the app has not run since it was installed or updated
        case notPaired                   // no key on this phone, or the Core refused the key
        case keyNotReadable              // the key cannot be read now: the phone has not been unlocked since it started
        case offline                     // the Core was not reached
        case noReading                   // the Core answered, but not with a reading (a fault on the PC)
        case reached(stopped: Bool, approvals: Int?, notices: Int?)   // nil: that count is not served to this phone
    }
    let date: Date
    let reading: Reading
}

struct StatusProvider: TimelineProvider {
    /// How soon iPhone is asked to draw the widget again; it decides, and draws it about this often at most.
    static let refresh: TimeInterval = 15 * 60

    func placeholder(in context: Context) -> StatusEntry { StatusEntry(date: Date(), reading: .gallery) }

    func getSnapshot(in context: Context, completion: @escaping (StatusEntry) -> Void) {
        guard !context.isPreview else {
            completion(StatusEntry(date: Date(), reading: .gallery))
            return
        }
        Task { @MainActor in completion(await Self.read()) }
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<StatusEntry>) -> Void) {
        Task { @MainActor in
            let entry = await Self.read()
            completion(Timeline(entries: [entry], policy: .after(Date().addingTimeInterval(Self.refresh))))
        }
    }

    /// The Core's `status` for this phone, with a short wait. A refused key is only shown: the app acts on it.
    @MainActor
    static func read() async -> StatusEntry {
        // The app shares the Core's address at its first start after an install or update; until then the widget
        // cannot tell a paired phone from one that is not.
        guard let address = AppSettings.address else { return StatusEntry(date: Date(), reading: .openApp) }
        let key: String
        switch Keychain.lookup() {
        case .found(let found): key = found
        case .notFound: return StatusEntry(date: Date(), reading: .notPaired)
        case .unreadable: return StatusEntry(date: Date(), reading: .keyNotReadable)
        }
        let client = HTTPCoreClient(address: address, credential: key)
        do {
            let info = try await client.status(timeout: 8)
            let approvals = (info.servesApprovals && info.approve) ? info.waiting : nil
            let notices = info.servesNotices ? info.notices : nil
            return StatusEntry(date: Date(), reading: .reached(stopped: info.stopped, approvals: approvals, notices: notices))
        } catch {
            let failure = error as? ClientFailure
            if let failure, failure.needsPairing { return StatusEntry(date: Date(), reading: .notPaired) }
            return StatusEntry(date: Date(), reading: failure == .unreachable ? .offline : .noReading)
        }
    }
}

struct StatusWidgetView: View {
    let entry: StatusEntry
    @Environment(\.widgetFamily) private var family

    var body: some View {
        if family == .systemMedium {
            HStack(spacing: 12) {
                summary
                if case .reached(_, let approvals, let notices) = entry.reading {
                    VStack(spacing: 8) {
                        count(approvals, one: "APPROVAL", many: "APPROVALS", link: "jarvis://approvals", warn: true)
                        count(notices, one: "NOTICE", many: "NOTICES", link: "jarvis://notices", warn: false)
                    }
                    .frame(width: 118)
                }
            }
            .widgetURL(URL(string: "jarvis://open"))
        } else {
            summary
                .widgetURL(URL(string: "jarvis://open"))
        }
    }

    /// The mark, the state, a line about it, and the time of the reading.
    private var summary: some View {
        VStack(alignment: .leading, spacing: 5) {
            HStack(spacing: 7) {
                JarvisMark().frame(width: 24, height: 24)
                Text("JARVIS").font(.system(size: 15, weight: .light)).foregroundStyle(Theme.text).lineLimit(1)
            }
            Spacer(minLength: 2)
            HStack(spacing: 6) {
                StatusDot(color: stateColor)
                Caption(stateWord, color: stateColor, size: 11).lineLimit(1)
            }
            ForEach(Array(detailLines.enumerated()), id: \.offset) { _, line in
                Text(line.text).font(.system(size: 11, weight: line.strong ? .semibold : .regular))
                    .foregroundStyle(line.strong ? Theme.warn : Theme.text.opacity(0.85))
                    .lineLimit(2)
                    .fixedSize(horizontal: false, vertical: true)
            }
            Spacer(minLength: 2)
            footer
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .leading)
    }

    @ViewBuilder private var footer: some View {
        switch entry.reading {
        case .gallery:
            Text("Tap to open").font(.system(size: 9)).foregroundStyle(Theme.muted)
        case .notPaired, .openApp:
            Text("Open JARVIS").font(.system(size: 9)).foregroundStyle(Theme.muted)
        default:
            Text("Checked \(entry.date, style: .time)").font(.system(size: 9)).foregroundStyle(Theme.muted)
        }
    }

    private var stateWord: String {
        switch entry.reading {
        case .gallery: return "Online or stopped"
        case .openApp: return "Open JARVIS"
        case .notPaired: return "Not paired"
        case .keyNotReadable, .noReading: return "No reading"
        case .offline: return "Offline"
        case .reached(let stopped, _, _): return stopped ? "Stopped" : "Online"
        }
    }

    private var stateColor: Color {
        switch entry.reading {
        case .gallery, .openApp, .notPaired, .keyNotReadable, .noReading: return Theme.muted
        case .offline: return Theme.warn
        case .reached(let stopped, _, _): return stopped ? Theme.bad : Theme.good
        }
    }

    /// The words under the state. The counts are said here on the small size; the medium size has its tiles.
    private var detailLines: [(text: String, strong: Bool)] {
        switch entry.reading {
        case .gallery:
            return [("Approvals and notices waiting for you", false)]
        case .openApp:
            return [("Open the app once to show JARVIS here.", false)]
        case .notPaired:
            return [("Open the app to pair this phone with JARVIS.", false)]
        case .keyNotReadable:
            return [("Unlock this phone once since it started.", false)]
        case .offline:
            return [("JARVIS was not reached from this phone.", false)]
        case .noReading:
            return [("JARVIS answered without a reading.", false)]
        case .reached(let stopped, let approvals, let notices):
            var lines: [(String, Bool)] = []
            if stopped { lines.append(("RESUME on the PC lifts the stop.", false)) }
            guard family != .systemMedium else { return lines }
            if let approvals, approvals > 0 { lines.append((approvals == 1 ? "1 approval waits" : "\(approvals) approvals wait", true)) }
            if let notices, notices > 0 { lines.append((notices == 1 ? "1 new notice" : "\(notices) new notices", false)) }
            if lines.isEmpty {
                // Only what the Core counts for this phone is said (approvals only with "May approve for JARVIS").
                switch (approvals, notices) {
                case (.some, .some): lines.append(("Nothing waits for you.", false))
                case (.some, nil): lines.append(("No approvals wait.", false))
                case (nil, .some): lines.append(("No new notices.", false))
                case (nil, nil): break
                }
            }
            return lines
        }
    }

    /// A count of the medium size: the number, what it counts, and a tap that opens that list. "—" when the Core
    /// does not count it for this phone (an older Core, or "May approve for JARVIS" not ticked).
    private func count(_ value: Int?, one: String, many: String, link: String, warn: Bool) -> some View {
        Link(destination: URL(string: link)!) {
            VStack(spacing: 2) {
                Text(value.map(String.init) ?? "—")
                    .font(.system(size: 24, weight: .light, design: .rounded))
                    .foregroundStyle((value ?? 0) > 0 ? (warn ? Theme.warn : Theme.accent) : Theme.text)
                Caption(value == 1 ? one : many, color: Theme.muted, size: 9).lineLimit(1)
            }
            .frame(maxWidth: .infinity, minHeight: 52)
            .background(Theme.ground.opacity(0.75))
            .overlay(RoundedRectangle(cornerRadius: 8).stroke(Theme.accent.opacity(0.3), lineWidth: 1))
            .clipShape(RoundedRectangle(cornerRadius: 8))
        }
    }
}

/// The widget's ground: the app's page, a cyan glow at the mark, a few fixed stars and a planet's lit edge low
/// across the bottom (the space scene of 2026-10-06).
struct WidgetGround: View {
    private static let stars: [(x: CGFloat, y: CGFloat, r: CGFloat, a: Double)] = [
        (0.08, 0.62, 1.2, 0.5), (0.18, 0.88, 0.8, 0.35), (0.31, 0.45, 1.0, 0.3), (0.42, 0.12, 0.9, 0.45),
        (0.55, 0.70, 1.3, 0.4), (0.63, 0.30, 0.8, 0.3), (0.71, 0.08, 1.1, 0.5), (0.79, 0.52, 0.9, 0.35),
        (0.86, 0.22, 1.4, 0.45), (0.93, 0.66, 0.8, 0.3), (0.26, 0.20, 0.7, 0.3), (0.48, 0.92, 1.0, 0.3)
    ]

    var body: some View {
        GeometryReader { g in
            ZStack {
                Theme.ground2
                RadialGradient(colors: [Theme.accent.opacity(0.16), .clear], center: UnitPoint(x: 0.15, y: 0.12),
                               startRadius: 4, endRadius: max(g.size.width, g.size.height) * 0.9)
                ForEach(Array(Self.stars.enumerated()), id: \.offset) { _, star in
                    Circle().fill(Color.white.opacity(star.a))
                        .frame(width: star.r * 2, height: star.r * 2)
                        .position(x: star.x * g.size.width, y: star.y * g.size.height)
                }
                let diameter = g.size.width * 2.8
                Circle().stroke(Theme.accent.opacity(0.25), lineWidth: 8).blur(radius: 9)
                    .frame(width: diameter, height: diameter)
                    .position(x: g.size.width * 0.5, y: g.size.height + diameter * 0.47)
                Circle().stroke(Theme.accent.opacity(0.5), lineWidth: 1.2)
                    .frame(width: diameter, height: diameter)
                    .position(x: g.size.width * 0.5, y: g.size.height + diameter * 0.47)
            }
        }
    }
}
