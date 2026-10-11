import SwiftUI

struct OrbitalGraphic: View {
    @State private var spin = false

    var body: some View {
        ZStack {
            Circle()
                .fill(
                    RadialGradient(
                        colors: [JARVISTheme.cyan.opacity(0.42), .clear],
                        center: .center,
                        startRadius: 4,
                        endRadius: 72
                    )
                )
                .frame(width: 116, height: 116)

            ForEach(0..<4, id: \.self) { i in
                Circle()
                    .stroke(JARVISTheme.cyan.opacity(i == 3 ? 0.14 : 0.34),
                            lineWidth: i == 3 ? 1 : 2)
                    .frame(
                        width: CGFloat(78 + i * 34),
                        height: CGFloat(78 + i * 34)
                    )
                    .rotationEffect(.degrees(spin ? 360 : 0))
                    .animation(
                        .linear(duration: Double(9 + i * 3))
                            .repeatForever(autoreverses: false),
                        value: spin
                    )
            }

            Circle()
                .trim(from: 0.05, to: 0.34)
                .stroke(JARVISTheme.cyan, style: StrokeStyle(lineWidth: 4, lineCap: .round))
                .frame(width: 142, height: 142)
                .rotationEffect(.degrees(spin ? 360 : 0))
                .animation(.linear(duration: 7).repeatForever(autoreverses: false), value: spin)

            Circle()
                .trim(from: 0.52, to: 0.78)
                .stroke(JARVISTheme.cyanSoft, style: StrokeStyle(lineWidth: 3, lineCap: .round))
                .frame(width: 104, height: 104)
                .rotationEffect(.degrees(spin ? -360 : 0))
                .animation(.linear(duration: 10).repeatForever(autoreverses: false), value: spin)

            Circle()
                .fill(JARVISTheme.cyan.opacity(0.28))
                .frame(width: 58, height: 58)
                .overlay(Circle().stroke(JARVISTheme.cyan.opacity(0.5), lineWidth: 1))
        }
        .onAppear { spin = true }
    }
}
