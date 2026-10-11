import SwiftUI

// The colour system of the design brief and the canvas (docs/PHONE-PLAN.md section 6). Nothing else is used.
// Shared since round 6 by the app, the widget and Share to JARVIS (JARVISShared/, in all three targets), so the
// three look alike. An image set an extension does not carry (the space scene) is simply left out, as in the app.
enum Theme {
    static let accent = Color(hex: 0x00D9FF)      // cyan, the main accent
    static let accent2 = Color(hex: 0x39BFFF)
    static let ground = Color(hex: 0x061522)      // panels
    static let ground2 = Color(hex: 0x02070D)     // the page
    static let text = Color(hex: 0xEAF7FF)
    static let muted = Color(hex: 0x7EA6BB)
    static let good = Color(hex: 0x39F5B5)
    static let warn = Color(hex: 0xFFC857)
    static let bad = Color(hex: 0xFF3B3B)

    static func caption(_ size: CGFloat = 10) -> Font { .system(size: size, weight: .semibold, design: .default) }
    static func mono(_ size: CGFloat = 11) -> Font { .system(size: size, weight: .regular, design: .monospaced) }
}

extension Color {
    init(hex: UInt32, opacity: Double = 1) {
        self.init(.sRGB,
                  red: Double((hex >> 16) & 0xFF) / 255,
                  green: Double((hex >> 8) & 0xFF) / 255,
                  blue: Double(hex & 0xFF) / 255,
                  opacity: opacity)
    }
}

/// The page ground: the space scene the owner chose (2026-10-06, "apply the look"), shown faintly under a shade so
/// the text stays readable, with the canvas's radial glow on top. Without the image set only the ground remains.
struct PageBackground: View {
    var body: some View {
        ZStack {
            Theme.ground2.ignoresSafeArea()
            StarField()   // round 6, the owner's picture of 2026-10-10: the stars of the space scene
            if UIImage(named: "JARVISBackground") != nil {   // the same guard as the badge: no log line, no empty image, when the set is missing
                Color.clear
                    .overlay(Image("JARVISBackground").resizable().scaledToFill())
                    .clipped()
                    .opacity(0.12)
                    .ignoresSafeArea()
                LinearGradient(colors: [.clear, Theme.ground2.opacity(0.85)], startPoint: .top, endPoint: .bottom)
                    .ignoresSafeArea()
            }
            RadialGradient(colors: [Theme.accent.opacity(0.10), .clear], center: .init(x: 0.5, y: 0.38),
                           startRadius: 10, endRadius: 320)
                .ignoresSafeArea()
            PlanetRims()   // round 6: a planet's lit edge across the top corner and low behind the tab bar
        }
        .accessibilityHidden(true)
    }
}

/// A fixed field of faint stars (the same on every screen and every launch: drawn from a fixed seed).
struct StarField: View {
    var body: some View {
        Canvas { context, size in
            var seed: UInt64 = 0x9E37_79B9_7F4A_7C15
            func next() -> Double {
                seed = seed &* 6_364_136_223_846_793_005 &+ 1_442_695_040_888_963_407
                return Double(seed >> 11) / Double(UInt64(1) << 53)
            }
            for _ in 0..<150 {
                let x = next() * size.width
                let y = next() * size.height
                let r = 0.5 + next() * 1.1
                let a = 0.12 + next() * 0.45
                context.fill(Path(ellipseIn: CGRect(x: x, y: y, width: r, height: r)), with: .color(.white.opacity(a)))
            }
        }
        .ignoresSafeArea()
        .allowsHitTesting(false)
    }
}

/// The lit edge of a planet, twice: across the top-left corner, and low behind the tab bar (the owner's picture).
struct PlanetRims: View {
    var body: some View {
        GeometryReader { g in
            let w = g.size.width
            let h = g.size.height
            ZStack {
                rim(diameter: w * 3.4, at: CGPoint(x: w * 0.5, y: h + w * 1.55), line: 0.55, glow: 0.35)
                rim(diameter: w * 2.6, at: CGPoint(x: -w * 0.25, y: -w * 1.05), line: 0.4, glow: 0.25)
            }
        }
        .ignoresSafeArea()
        .allowsHitTesting(false)
    }

    private func rim(diameter: CGFloat, at center: CGPoint, line: Double, glow: Double) -> some View {
        ZStack {
            Circle().stroke(Theme.accent.opacity(glow), lineWidth: 10).blur(radius: 12)
            Circle().stroke(Theme.accent.opacity(line), lineWidth: 1.5).blur(radius: 0.6)
        }
        .frame(width: diameter, height: diameter)
        .position(center)
    }
}

/// A bordered panel with the canvas's corner marks.
struct Panel<Content: View>: View {
    var marked = true
    @ViewBuilder var content: () -> Content

    var body: some View {
        content()
            .padding(12)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(LinearGradient(colors: [Theme.ground.opacity(0.85), Color(hex: 0x040F1A).opacity(0.92)],
                                       startPoint: .top, endPoint: .bottom))
            .overlay(Rectangle().stroke(Theme.accent.opacity(0.25), lineWidth: 1))
            .overlay(alignment: .topLeading) { if marked { CornerMark(flipped: false) } }
            .overlay(alignment: .bottomTrailing) { if marked { CornerMark(flipped: true) } }
    }
}

struct CornerMark: View {
    let flipped: Bool
    var body: some View {
        Path { p in
            p.move(to: CGPoint(x: 0, y: 10)); p.addLine(to: CGPoint(x: 0, y: 0)); p.addLine(to: CGPoint(x: 10, y: 0))
        }
        .stroke(Theme.accent, lineWidth: 1)
        .frame(width: 10, height: 10)
        .rotationEffect(.degrees(flipped ? 180 : 0))
    }
}

/// Small upper-case caption, as the canvas labels things.
struct Caption: View {
    let text: String
    var color: Color = Theme.muted
    var size: CGFloat = 10
    init(_ text: String, color: Color = Theme.muted, size: CGFloat = 10) { self.text = text; self.color = color; self.size = max(9, size) }   // never below 9 pt on a phone
    var body: some View {
        Text(text.uppercased()).font(Theme.caption(size)).foregroundStyle(color).tracking(1.2)
    }
}

/// The small dot that says "online", "good", "warning" or "stopped".
struct StatusDot: View {
    var color: Color = Theme.good
    var body: some View { Circle().fill(color).frame(width: 6, height: 6) }
}

/// The thin cyan rule under the header.
struct HeaderRule: View {
    var body: some View {
        ZStack(alignment: .leading) {
            LinearGradient(colors: [.clear, Theme.accent.opacity(0.35), Theme.accent.opacity(0.35), .clear],
                           startPoint: .leading, endPoint: .trailing).frame(height: 1)
            Rectangle().fill(Theme.accent).frame(width: 110, height: 2)
        }
        .frame(height: 8, alignment: .center)
    }
}

/// The header every screen shares: the mark, JARVIS, a subtitle line, and whatever sits at the right.
struct ScreenHeader<Trailing: View>: View {
    let subtitle: String
    @ViewBuilder var trailing: () -> Trailing

    var body: some View {
        VStack(spacing: 6) {
            HStack(alignment: .center, spacing: 10) {
                JarvisMark().frame(width: 40, height: 40)
                VStack(alignment: .leading, spacing: 3) {
                    Text("JARVIS").font(.system(size: 20, weight: .light)).foregroundStyle(Theme.text).lineLimit(1).minimumScaleFactor(0.85)
                    Caption(subtitle, color: Theme.accent, size: 9).lineLimit(1)   // cut, never shrunk under 9 pt
                }
                .layoutPriority(0)
                Spacer(minLength: 6)
                // At the phone's width the right-hand items keep their full size and the subtitle gives way (cut
                // with "…"): never a wrapped ONLINE or a STOP ALL squeezed to "S" (docs/PHONE-V1-RESULT.md, item 4).
                trailing()
                    .fixedSize(horizontal: true, vertical: false)
                    .layoutPriority(1)
            }
            .frame(height: 44)
            HeaderRule()
        }
    }
}

/// The logo of every header: the Teague Industries badge in a cyan ring (the owner's choice of 2026-10-06). If the
/// image set is missing from the project, the drawn T mark of the first build stands in.
struct JarvisMark: View {
    var body: some View {
        if UIImage(named: "TeagueBadge") != nil {
            Image("TeagueBadge")
                .resizable()
                .scaledToFill()
                .clipShape(Circle())
                .overlay(Circle().stroke(Theme.accent.opacity(0.55), lineWidth: 1))
                .shadow(color: Theme.accent.opacity(0.25), radius: 5)
                .accessibilityLabel("Teague Industries")
        } else {
            ZStack {
                Circle().stroke(Theme.accent.opacity(0.6), lineWidth: 1)
                Circle().stroke(Theme.accent.opacity(0.25), lineWidth: 1).padding(4)
                Text("T").font(.system(size: 16, weight: .semibold, design: .serif)).foregroundStyle(Theme.text)
            }
        }
    }
}

/// A rounded icon button of the header (34 x 34, cyan on ground).
struct IconButton: View {
    let system: String
    let label: String
    let action: () -> Void
    var body: some View {
        Button(action: action) {
            Image(systemName: system).font(.system(size: 14, weight: .medium)).foregroundStyle(Theme.accent)
                .frame(width: 34, height: 34)
                .background(Theme.ground.opacity(0.6))
                .overlay(RoundedRectangle(cornerRadius: 8).stroke(Theme.accent.opacity(0.25), lineWidth: 1))
                .frame(width: 44, height: 44)   // the touch target: 44 pt, the drawn button inside it
                .contentShape(Rectangle())
        }
        .accessibilityLabel(label)
    }
}

/// The red STOP ALL control: the emergency stop that any paired device may raise and none may lift.
struct StopButton: View {
    let stopped: Bool
    let action: () -> Void
    var body: some View {
        Button(action: action) {
            HStack(spacing: 6) {
                Circle().fill(Theme.bad).frame(width: 6, height: 6)
                Text(stopped ? "STOPPED" : "STOP ALL").font(Theme.caption(9)).tracking(1.2)
            }
            .foregroundStyle(stopped ? Theme.text : Theme.bad)
            .padding(.horizontal, 10).frame(height: 30)
            .background(stopped ? Theme.bad.opacity(0.45) : Theme.bad.opacity(0.12))
            .overlay(RoundedRectangle(cornerRadius: 6).stroke(Theme.bad.opacity(0.7), lineWidth: 1))
            .frame(minHeight: 44)   // the touch target
            .contentShape(Rectangle())
        }
        .disabled(stopped)
        .accessibilityLabel(stopped ? "Emergency stop is on" : "Emergency stop: stop everything")
    }
}
