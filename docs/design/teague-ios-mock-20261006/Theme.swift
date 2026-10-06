import SwiftUI

enum JARVISTheme {
    static let cyan = Color(red: 0.05, green: 0.72, blue: 1.0)
    static let cyanSoft = Color(red: 0.04, green: 0.42, blue: 0.58)
    static let background = Color(red: 0.008, green: 0.025, blue: 0.045)
    static let panel = Color(red: 0.015, green: 0.055, blue: 0.08)
    static let panel2 = Color(red: 0.02, green: 0.075, blue: 0.105)
    static let text = Color.white
    static let secondary = Color.white.opacity(0.58)
}

struct GlassPanel: ViewModifier {
    var radius: CGFloat = 18
    func body(content: Content) -> some View {
        content
            .background(
                RoundedRectangle(cornerRadius: radius, style: .continuous)
                    .fill(.ultraThinMaterial.opacity(0.52))
                    .overlay(
                        RoundedRectangle(cornerRadius: radius, style: .continuous)
                            .stroke(JARVISTheme.cyan.opacity(0.28), lineWidth: 1)
                    )
            )
    }
}

extension View {
    func jarvisGlass(radius: CGFloat = 18) -> some View {
        modifier(GlassPanel(radius: radius))
    }
}
