import SwiftUI

struct PairingView: View {
    @AppStorage("jarvis.paired") private var paired = false
    @State private var address = ""
    @State private var port = "8790"
    @State private var code = ""
    @State private var showingError = false
    @FocusState private var focusedField: Field?

    enum Field { case address, port, code }

    var body: some View {
        ZStack {
            background

            ScrollView(showsIndicators: false) {
                VStack(spacing: 0) {
                    header
                    progress

                    OrbitalGraphic()
                        .frame(height: 205)
                        .padding(.top, 4)

                    VStack(spacing: 18) {
                        fieldSection(
                            title: "WHERE JARVIS IS",
                            description: "The PC's Tailscale name or address, as Settings > Devices > Private network shows it on the PC, and the door's port (8790 unless you changed it)."
                        ) {
                            field("Tailscale name or address", text: $address, field: .address)
                            field("8790", text: $port, field: .port, keyboard: .numberPad)
                        }

                        fieldSection(
                            title: "THE CODE",
                            description: "On the PC: Settings > Devices, name this phone, kind phone, PAIR A DEVICE. Type the eight digits it shows."
                        ) {
                            field("8-digit code", text: $code, field: .code, keyboard: .numberPad)
                        }

                        Button(action: pair) {
                            HStack {
                                Spacer()
                                Text("PAIR")
                                    .font(.system(size: 17, weight: .bold, design: .rounded))
                                    .tracking(4)
                                Spacer()
                            }
                            .frame(height: 58)
                            .background(
                                LinearGradient(
                                    colors: [JARVISTheme.cyanSoft, JARVISTheme.cyan.opacity(0.72)],
                                    startPoint: .leading,
                                    endPoint: .trailing
                                )
                            )
                            .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
                            .overlay(
                                RoundedRectangle(cornerRadius: 10)
                                    .stroke(JARVISTheme.cyan.opacity(0.65), lineWidth: 1)
                            )
                        }
                        .buttonStyle(.plain)
                        .disabled(address.isEmpty || code.count != 8)

                        privacy

                        if showingError {
                            Text("Enter the PC address and an 8-digit pairing code.")
                                .font(.caption)
                                .foregroundStyle(.red.opacity(0.85))
                                .transition(.opacity)
                        }
                    }
                    .padding(.horizontal, 28)
                    .padding(.bottom, 30)
                }
            }
        }
        .ignoresSafeArea(edges: .bottom)
    }

    private var background: some View {
        ZStack {
            JARVISTheme.background.ignoresSafeArea()
            Image("JARVISBackground")
                .resizable()
                .scaledToFill()
                .opacity(0.12)
                .blur(radius: 0.5)
                .ignoresSafeArea()
            LinearGradient(
                colors: [.black.opacity(0.05), JARVISTheme.background.opacity(0.88)],
                startPoint: .top,
                endPoint: .bottom
            )
            .ignoresSafeArea()
        }
    }

    private var header: some View {
        HStack(spacing: 14) {
            Image("TeagueLogo")
                .resizable()
                .scaledToFill()
                .frame(width: 46, height: 46)
                .clipShape(Circle())
                .overlay(Circle().stroke(JARVISTheme.cyan.opacity(0.55), lineWidth: 1))

            VStack(alignment: .leading, spacing: 2) {
                Text("JARVIS")
                    .font(.system(size: 22, weight: .medium, design: .rounded))
                    .tracking(1)
                Text("PAIR THIS PHONE")
                    .font(.system(size: 12, weight: .bold, design: .rounded))
                    .tracking(2.5)
                    .foregroundStyle(JARVISTheme.cyan)
            }

            Spacer()
        }
        .padding(.horizontal, 28)
        .padding(.top, 18)
    }

    private var progress: some View {
        GeometryReader { proxy in
            ZStack(alignment: .leading) {
                Rectangle().fill(JARVISTheme.cyan.opacity(0.18))
                Rectangle()
                    .fill(JARVISTheme.cyan)
                    .frame(width: proxy.size.width * 0.30)
                    .shadow(color: JARVISTheme.cyan, radius: 5)
            }
        }
        .frame(height: 2)
        .padding(.top, 18)
    }

    private func fieldSection<Content: View>(
        title: String,
        description: String,
        @ViewBuilder content: () -> Content
    ) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title)
                .font(.system(size: 17, weight: .bold, design: .rounded))
                .tracking(1.2)

            Text(description)
                .font(.system(size: 14, weight: .medium, design: .rounded))
                .foregroundStyle(JARVISTheme.secondary)
                .lineSpacing(3)

            VStack(spacing: 10) {
                content()
            }
            .padding(12)
            .jarvisGlass(radius: 12)
        }
    }

    private func field(
        _ placeholder: String,
        text: Binding<String>,
        field: Field,
        keyboard: UIKeyboardType = .default
    ) -> some View {
        TextField(placeholder, text: text)
            .textInputAutocapitalization(.never)
            .autocorrectionDisabled()
            .keyboardType(keyboard)
            .focused($focusedField, equals: field)
            .font(.system(size: 16, weight: .medium, design: .monospaced))
            .foregroundStyle(.white)
            .padding(.horizontal, 16)
            .frame(height: 58)
            .background(JARVISTheme.panel2.opacity(0.8))
            .overlay(
                RoundedRectangle(cornerRadius: 7)
                    .stroke(
                        focusedField == field ? JARVISTheme.cyan.opacity(0.72) : JARVISTheme.cyan.opacity(0.18),
                        lineWidth: 1
                    )
            )
            .clipShape(RoundedRectangle(cornerRadius: 7))
    }

    private var privacy: some View {
        Text("This phone declares its microphone, speakers and display. What the owner ticks on the PC is what it may use. The phone keeps only its key (in the Keychain), the Core's address and name, which conversation is open, and the speak-replies choice. The conversations themselves stay on the PC.")
            .font(.system(size: 13, weight: .medium, design: .rounded))
            .foregroundStyle(JARVISTheme.secondary)
            .lineSpacing(3)
            .padding(.horizontal, 18)
            .padding(.top, 4)
    }

    private func pair() {
        guard !address.isEmpty, code.count == 8 else {
            withAnimation { showingError = true }
            return
        }
        showingError = false
        paired = true
    }
}

#Preview {
    PairingView()
}
