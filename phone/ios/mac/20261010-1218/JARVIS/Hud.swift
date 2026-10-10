import SwiftUI

// The panel kit of the command look (ROUND3-COMMAND-LOOK.md): the chrome of the owner's picture, drawn with the
// colour system of the design brief. Nothing here invents a value: every number is passed in by the screen.

/// A dark panel with two cut corners, a cyan rule, and a title row with a status word on the right.
struct HudPanel<Content: View>: View {
    let title: String
    var status: String? = nil
    var statusColor: Color = Theme.accent
    @ViewBuilder var content: () -> Content

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(alignment: .firstTextBaseline, spacing: 8) {
                Text(title.uppercased()).font(.system(size: 12, weight: .semibold)).foregroundStyle(Theme.text).tracking(1.4)
                    .lineLimit(1).layoutPriority(1)
                Spacer(minLength: 6)
                if let status {
                    Caption(status, color: statusColor, size: 9).lineLimit(1)   // never shrunk: captions stay 9 pt
                }
            }
            Rectangle()
                .fill(LinearGradient(colors: [Theme.accent.opacity(0.55), Theme.accent.opacity(0.05)], startPoint: .leading, endPoint: .trailing))
                .frame(height: 1)
            content()
        }
        .padding(12)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            CutCornerRect(cut: 10)
                .fill(LinearGradient(colors: [Theme.ground.opacity(0.88), Color(hex: 0x040F1A).opacity(0.94)], startPoint: .top, endPoint: .bottom))
        )
        .overlay(CutCornerRect(cut: 10).stroke(Theme.accent.opacity(0.28), lineWidth: 1))
    }
}

/// A rectangle with its top-left and bottom-right corners cut off, as the picture's panels are.
struct CutCornerRect: Shape {
    var cut: CGFloat = 10

    func path(in r: CGRect) -> Path {
        var p = Path()
        p.move(to: CGPoint(x: r.minX + cut, y: r.minY))
        p.addLine(to: CGPoint(x: r.maxX, y: r.minY))
        p.addLine(to: CGPoint(x: r.maxX, y: r.maxY - cut))
        p.addLine(to: CGPoint(x: r.maxX - cut, y: r.maxY))
        p.addLine(to: CGPoint(x: r.minX, y: r.maxY))
        p.addLine(to: CGPoint(x: r.minX, y: r.minY + cut))
        p.closeSubpath()
        return p
    }
}

/// The brand line on the left and the real clock on the right, under the header. The clock is the phone's own.
struct HudStrip: View {
    var body: some View {
        TimelineView(.everyMinute) { context in
            HStack(alignment: .center, spacing: 8) {
                VStack(alignment: .leading, spacing: 3) {
                    Caption("Teague Industries", color: Theme.text, size: 9)
                    Caption("Intelligence amplifies humanity", size: 9).lineLimit(1)
                }
                Spacer(minLength: 8)
                VStack(alignment: .trailing, spacing: 2) {
                    Text(context.date.formatted(.dateTime.hour().minute()))
                        .font(.system(size: 20, weight: .light)).monospacedDigit().foregroundStyle(Theme.text)
                    Caption(context.date.formatted(.dateTime.weekday(.abbreviated).day().month(.abbreviated)), size: 9)
                }
                .fixedSize()
            }
            .padding(.horizontal, 4)
        }
        .accessibilityElement(children: .combine)
    }
}

/// A small line of recent values, as the picture's tiles have. Scaled between the lowest and highest value seen,
/// with a floor on the range, so a steady reading draws flat instead of as noise. `closed` gives the area under
/// the line, for a faint fill.
struct Sparkline: Shape {
    let values: [Double]
    var closed = false
    var minimumRange: Double = 5

    func path(in rect: CGRect) -> Path {
        var p = Path()
        // Fewer than two samples: nothing is drawn (a line at mid-height would read as a 50 % value).
        guard values.count >= 2, let lo = values.min(), let hi = values.max() else { return p }
        let range = max(hi - lo, minimumRange)
        let bottom = (hi + lo) / 2 - range / 2
        let step = rect.width / CGFloat(values.count - 1)
        for (i, v) in values.enumerated() {
            let x = rect.minX + CGFloat(i) * step
            let y = rect.maxY - CGFloat((v - bottom) / range) * rect.height
            if i == 0 { p.move(to: CGPoint(x: x, y: y)) } else { p.addLine(to: CGPoint(x: x, y: y)) }
        }
        if closed {
            p.addLine(to: CGPoint(x: rect.maxX, y: rect.maxY))
            p.addLine(to: CGPoint(x: rect.minX, y: rect.maxY))
            p.closeSubpath()
        }
        return p
    }
}

/// A ring filled to a share, as the picture's "100% operational" ring.
struct ProgressRing: View {
    let share: Double
    let color: Color
    var lineWidth: CGFloat = 5

    var body: some View {
        ZStack {
            Circle().stroke(Theme.accent.opacity(0.12), lineWidth: lineWidth)
            Circle().trim(from: 0, to: min(1, max(0, share)))
                .stroke(color, style: StrokeStyle(lineWidth: lineWidth, lineCap: .round))
                .rotationEffect(.degrees(-90))
        }
    }
}

/// One diagnostics tile: a label, the value with its unit, a sparkline of the recent values. Percent tiles turn
/// amber above 75 and red above 90, as the old gauges did.
struct DiagnosticTile: View {
    let label: String
    let value: Double?
    let unit: String
    let history: [Double]

    private var color: Color {
        guard let value else { return Theme.muted }
        if unit == "%" {
            if value > 90 { return Theme.bad }
            if value > 75 { return Theme.warn }
        }
        return Theme.accent
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Caption(label, size: 9)
            HStack(alignment: .firstTextBaseline, spacing: 2) {
                Text(value.map { "\(Int($0.rounded()))" } ?? "—")
                    .font(.system(size: 24, weight: .light)).monospacedDigit().foregroundStyle(Theme.text)
                Text(unit).font(.system(size: 11)).foregroundStyle(Theme.muted)
            }
            ZStack {
                Sparkline(values: history, closed: true)
                    .fill(LinearGradient(colors: [color.opacity(0.35), .clear], startPoint: .top, endPoint: .bottom))
                Sparkline(values: history)
                    .stroke(color, style: StrokeStyle(lineWidth: 1.5, lineCap: .round, lineJoin: .round))
            }
            .frame(height: 28)
        }
        .padding(10)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Theme.ground2.opacity(0.5))
        .overlay(Rectangle().stroke(Theme.accent.opacity(0.18), lineWidth: 1))
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("\(label): \(value.map { "\(Int($0.rounded())) \(unit)" } ?? "not read")")
    }
}

/// Bars of the recent microphone levels (0 to 1 each) during a hold; the empty slots stay as a faint baseline.
struct WaveformBars: View {
    let levels: [Double]
    var count = 36
    var color: Color = Theme.accent

    var body: some View {
        GeometryReader { geo in
            let shown = Array(levels.suffix(count))
            let slot = geo.size.width / CGFloat(count)
            HStack(spacing: 0) {
                ForEach(0..<count, id: \.self) { i in
                    let index = i - (count - shown.count)
                    let level = index >= 0 ? shown[index] : 0
                    RoundedRectangle(cornerRadius: 1)
                        .fill(color.opacity(index >= 0 ? 0.9 : 0.25))
                        .frame(width: max(1, slot * 0.5), height: max(2, CGFloat(level) * geo.size.height))
                        .frame(width: slot, height: geo.size.height)
                }
            }
        }
        .accessibilityHidden(true)
    }
}

/// The header's state dot and word, the same rule on every screen that has one: short words only, because at the
/// phone's width a long word costs the title its room (the round 2 run of 2026-10-07 showed "JA…" beside
/// NOT REACHED). The full sentence is under the core on Ask.
struct HeaderState: View {
    let state: JarvisState

    private var color: Color {
        switch state {
        case .offline: return Theme.muted
        case .stopped, .error: return Theme.bad
        default: return Theme.good
        }
    }

    private var word: String {
        switch state {
        case .offline: return "Offline"
        case .stopped: return "Stopped"
        default: return "Online"
        }
    }

    var body: some View {
        HStack(spacing: 6) {
            StatusDot(color: color)
            Caption(word, color: Theme.text, size: 9)
        }
    }
}

/// What the app says about itself: the version from the bundle, never a typed number.
enum AppInfo {
    static var version: String {
        Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "—"
    }
}
