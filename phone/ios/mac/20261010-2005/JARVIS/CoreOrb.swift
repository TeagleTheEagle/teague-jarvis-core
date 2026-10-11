import SwiftUI

/// The glowing core of the command look (ROUND3-COMMAND-LOOK.md, the owner's orb picture): a bright nucleus,
/// three tilted rings turning slowly, thin rings with ticks, four bright arcs on the outer ring, a faint crosshair
/// with bright nodes. Colour and speed follow JARVIS's state as the Ask screen's rings did: cyan standing by,
/// green while listening (the glow widens with the microphone level), amber while thinking or working, red when
/// stopped, grey and still when the Core is not reached. Still when the system's Reduce Motion is on.
struct CoreOrb: View {
    let state: JarvisState
    var level: Double = 0
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    // The motion's phase is carried across state changes (review of round 3, finding 10): a new speed changes the
    // pace, never the angle. `anchor` is the moment of the last change, `phaseAtAnchor` the phase reached then.
    @State private var anchor = Date()
    @State private var phaseAtAnchor = 0.0

    private var color: Color {
        switch state {
        case .offline: return Theme.muted
        case .listening: return Theme.good
        case .thinking, .executing: return Theme.warn
        case .stopped, .error: return Theme.bad
        default: return Theme.accent
        }
    }

    private static func speed(for state: JarvisState) -> Double {
        switch state {
        case .offline, .stopped: return 0
        case .thinking, .executing: return 2.4
        case .listening, .speaking: return 1.4
        default: return 0.6
        }
    }

    private var speed: Double { Self.speed(for: state) }

    var body: some View {
        let still = reduceMotion || speed == 0
        TimelineView(.animation(minimumInterval: 1.0 / 30, paused: still)) { context in
            let t = still ? phaseAtAnchor : phaseAtAnchor + context.date.timeIntervalSince(anchor) * speed
            let lift = state == .listening ? min(1, max(0, level)) : 0   // the microphone widens the glow only while listening
            Canvas { ctx, size in
                let c = CGPoint(x: size.width / 2, y: size.height / 2)
                let radius = min(size.width, size.height) / 2
                let col = color

                // The glow behind everything; wider while listening.
                ctx.fill(Path(ellipseIn: square(c, radius * 1.3)),
                         with: .radialGradient(Gradient(colors: [col.opacity(0.32 + lift * 0.3), col.opacity(0.05), .clear]),
                                               center: c, startRadius: 0, endRadius: radius * 0.65))

                // The crosshair.
                var cross = Path()
                cross.move(to: CGPoint(x: c.x - radius, y: c.y)); cross.addLine(to: CGPoint(x: c.x + radius, y: c.y))
                cross.move(to: CGPoint(x: c.x, y: c.y - radius)); cross.addLine(to: CGPoint(x: c.x, y: c.y + radius))
                ctx.stroke(cross, with: .color(col.opacity(0.12)), lineWidth: 0.5)

                // Thin rings, a dotted ring, the ticks.
                ctx.stroke(Path(ellipseIn: square(c, radius * 1.94)), with: .color(col.opacity(0.18)), lineWidth: 1)
                ctx.stroke(Path(ellipseIn: square(c, radius * 1.64)), with: .color(col.opacity(0.14)), lineWidth: 1)
                ctx.stroke(Path(ellipseIn: square(c, radius * 0.60)), with: .color(col.opacity(0.35)), lineWidth: 1)
                ctx.stroke(Path(ellipseIn: square(c, radius * 1.80)), with: .color(col.opacity(0.35)),
                           style: StrokeStyle(lineWidth: 1, dash: [2, 6]))
                var ticks = Path()
                for i in 0..<36 {
                    let angle = Double(i) / 36 * 2 * .pi
                    let inner = radius * (i % 9 == 0 ? 0.82 : 0.85)
                    let outer = radius * 0.88
                    ticks.move(to: CGPoint(x: c.x + cos(angle) * inner, y: c.y + sin(angle) * inner))
                    ticks.addLine(to: CGPoint(x: c.x + cos(angle) * outer, y: c.y + sin(angle) * outer))
                }
                ctx.stroke(ticks, with: .color(col.opacity(0.45)), lineWidth: 1)

                // Four bright arcs on the outer ring, turning one way.
                for i in 0..<4 {
                    let start = Angle.radians(Double(i) * .pi / 2 - t * 0.35)
                    var arc = Path()
                    arc.addArc(center: c, radius: radius * 0.97, startAngle: start, endAngle: start + .radians(0.55), clockwise: false)
                    ctx.stroke(arc, with: .color(col.opacity(0.9)), style: StrokeStyle(lineWidth: 3, lineCap: .round))
                }

                // Three tilted rings ("petals") turning the other way, each with a soft edge.
                for i in 0..<3 {
                    let tilt = Double(i) * .pi / 3 + t * 0.25
                    let petal = Path(ellipseIn: CGRect(x: -radius * 0.62, y: -radius * 0.34, width: radius * 1.24, height: radius * 0.68))
                        .applying(CGAffineTransform(rotationAngle: tilt))
                        .applying(CGAffineTransform(translationX: c.x, y: c.y))
                    ctx.stroke(petal, with: .color(col.opacity(0.18)), lineWidth: 5)
                    ctx.stroke(petal, with: .color(col.opacity(0.6)), lineWidth: 1.2)
                }

                // The nucleus: white-hot centre, the colour around it.
                let core = radius * (0.16 + lift * 0.06)
                ctx.fill(Path(ellipseIn: square(c, core * 2.4)),
                         with: .radialGradient(Gradient(colors: [col.opacity(0.6), .clear]), center: c, startRadius: 0, endRadius: core * 1.2))
                ctx.fill(Path(ellipseIn: square(c, core)),
                         with: .radialGradient(Gradient(colors: [Theme.text.opacity(0.95), col, col.opacity(0.1)]), center: c, startRadius: 0, endRadius: core / 2))

                // Bright nodes where the crosshair meets the outer ring.
                for (dx, dy) in [(1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0)] {
                    let p = CGPoint(x: c.x + dx * radius * 0.97, y: c.y + dy * radius * 0.97)
                    ctx.fill(Path(ellipseIn: CGRect(x: p.x - 2.5, y: p.y - 2.5, width: 5, height: 5)), with: .color(Theme.text.opacity(0.9)))
                }
            }
        }
        .aspectRatio(1, contentMode: .fit)
        .accessibilityHidden(true)
        .onChange(of: state) { previous, _ in
            let now = Date()
            phaseAtAnchor += now.timeIntervalSince(anchor) * Self.speed(for: previous)
            anchor = now
        }
    }

    private func square(_ c: CGPoint, _ diameter: CGFloat) -> CGRect {
        CGRect(x: c.x - diameter / 2, y: c.y - diameter / 2, width: diameter, height: diameter)
    }
}
