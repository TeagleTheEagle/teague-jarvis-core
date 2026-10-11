import SwiftUI

/// Before the three screens: pair this phone with the code the owner reads from the PC
/// (Settings > Devices > PAIR A DEVICE; the code is good for five minutes and one use).
struct PairingView: View {
    @EnvironmentObject private var session: SessionModel
    @State private var host: String = AppSettings.address?.host ?? ""
    @State private var port: String = String(AppSettings.address?.port ?? CoreAddress.defaultPort)
    @State private var code = ""
    @State private var working = false
    @State private var note: String?
    @FocusState private var focus: Field?
    enum Field { case host, port, code }

    var body: some View {
        ZStack {
            PageBackground()
            ScrollView {
                VStack(spacing: 14) {
                    ScreenHeader(subtitle: "Pair this phone") { EmptyView() }
                    OrbitalGraphic().frame(height: 200).padding(.top, 6)
                    if let notice = session.notice {
                        Text(notice).font(.system(size: 11)).foregroundStyle(Theme.warn).multilineTextAlignment(.center)
                    }
                    Panel {
                        VStack(alignment: .leading, spacing: 10) {
                            Text("WHERE JARVIS IS").font(.system(size: 11, weight: .semibold)).foregroundStyle(Theme.text)
                            Text("The PC's Tailscale name or address, as Settings > Devices > Private network shows it on the PC, and the door's port (8790 unless you changed it).")
                                .font(.system(size: 11)).foregroundStyle(Theme.muted)
                            field("Tailscale name or address", text: $host, field: .host, keyboard: .URL)
                            field("Port", text: $port, field: .port, keyboard: .numberPad)
                        }
                    }
                    Panel {
                        VStack(alignment: .leading, spacing: 10) {
                            Text("THE CODE").font(.system(size: 11, weight: .semibold)).foregroundStyle(Theme.text)
                            Text("On the PC: Settings > Devices, name this phone, kind phone, PAIR A DEVICE. Type the eight digits it shows.")
                                .font(.system(size: 11)).foregroundStyle(Theme.muted)
                            field("8-digit code", text: $code, field: .code, keyboard: .numberPad)
                                .onChange(of: code) { _, value in code = String(value.filter(\.isNumber).prefix(8)) }
                        }
                    }
                    if let note {
                        Text(note).font(.system(size: 11)).foregroundStyle(Theme.warn).multilineTextAlignment(.center)
                    }
                    Button {
                        Task { await pair() }
                    } label: {
                        HStack {
                            if working { ProgressView().tint(Theme.ground2) }
                            Text(working ? "PAIRING…" : "PAIR").font(Theme.caption(12)).tracking(1.5)
                        }
                        .frame(maxWidth: .infinity).frame(height: 46)
                        .background(canPair ? Theme.accent : Theme.accent.opacity(0.3))
                        .foregroundStyle(Theme.ground2)
                    }
                    .disabled(!canPair || working)
                    Text("This phone declares its microphone, speakers and display. What the owner ticks on the PC is what it may use. The phone keeps only its key (in the Keychain), the Core's address and name, which conversation is open, the speak-replies and Face ID choices, and a question Siri took until it is sent. The conversations themselves stay on the PC.")
                        .font(.system(size: 10)).foregroundStyle(Theme.muted.opacity(0.8)).multilineTextAlignment(.center)
                }
                .padding(.horizontal, 16).padding(.bottom, 24)
            }
            .scrollDismissesKeyboard(.interactively)
        }
    }

    private var canPair: Bool {
        !host.trimmingCharacters(in: .whitespaces).isEmpty && Int(port) != nil && code.count == 8
    }

    private func field(_ label: String, text: Binding<String>, field: Field, keyboard: UIKeyboardType) -> some View {
        TextField(label, text: text)
            .font(field == .code ? Theme.mono(18) : .system(size: 14))
            .foregroundStyle(Theme.text)
            .keyboardType(keyboard)
            .textInputAutocapitalization(.never)
            .autocorrectionDisabled()
            .focused($focus, equals: field)
            .padding(.horizontal, 12).frame(height: 42)
            .background(Theme.ground.opacity(0.7))
            .overlay(Rectangle().stroke(Theme.accent.opacity(focus == field ? 0.7 : 0.25), lineWidth: 1))
    }

    private func pair() async {
        guard let portNumber = Int(port) else { note = ClientFailure.invalidAddress.errorDescription; return }
        working = true
        note = nil
        defer { working = false }
        do {
            try await session.pair(host: host, port: portNumber, code: code)
            code = ""
        } catch {
            note = (error as? ClientFailure)?.errorDescription ?? "Pairing did not work."
        }
    }
}

/// The orbital graphic of the pairing screen (the owner's "apply the look", 2026-10-06): a soft halo, three faint
/// rings, three arcs turning slowly, a glowing core. Built like the Ask screen's rings of version 1 (the Ask screen
/// now has the CoreOrb of round 3); still when the system's Reduce Motion is on.
struct OrbitalGraphic: View {
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        TimelineView(.animation(minimumInterval: 1.0 / 30, paused: reduceMotion)) { context in
            let t = reduceMotion ? 0 : context.date.timeIntervalSinceReferenceDate
            ZStack {
                Circle()
                    .fill(RadialGradient(colors: [Theme.accent.opacity(0.30), .clear], center: .center, startRadius: 2, endRadius: 92))
                    .padding(8)
                Circle().stroke(Theme.accent.opacity(0.15), lineWidth: 1)
                Circle().stroke(Theme.accent.opacity(0.25), lineWidth: 1).padding(22)
                Circle().stroke(Theme.accent.opacity(0.35), lineWidth: 1).padding(48)
                Circle().trim(from: 0, to: 0.28).stroke(Theme.accent, style: StrokeStyle(lineWidth: 3, lineCap: .round))
                    .padding(10).rotationEffect(.degrees(t * 36))
                Circle().trim(from: 0, to: 0.18).stroke(Theme.accent.opacity(0.8), style: StrokeStyle(lineWidth: 2, lineCap: .round))
                    .padding(10).rotationEffect(.degrees(-t * 36 + 150))
                Circle().trim(from: 0, to: 0.42).stroke(Theme.accent2.opacity(0.7), style: StrokeStyle(lineWidth: 2, lineCap: .round))
                    .padding(32).rotationEffect(.degrees(-t * 24 + 95))
                Circle()
                    .fill(RadialGradient(colors: [Theme.accent.opacity(0.45), Theme.ground.opacity(0.1)], center: .center, startRadius: 2, endRadius: 40))
                    .padding(60)   // a 200 pt graphic: the core is 80 pt across, so the glow ends at its edge (review note 1)
                Circle().stroke(Theme.accent.opacity(0.5), lineWidth: 1).padding(71)
            }
        }
        .aspectRatio(1, contentMode: .fit)
        .accessibilityHidden(true)
    }
}

/// The small settings sheet: where the Core is, how replies are spoken, forget this pairing, about.
struct SettingsSheet: View {
    @EnvironmentObject private var session: SessionModel
    @Environment(\.dismiss) private var dismiss
    @State private var confirmForget = false

    var body: some View {
        NavigationStack {
            ZStack {
                PageBackground()
                ScrollView {
                    VStack(spacing: 12) {
                        Panel(marked: false) {
                            VStack(alignment: .leading, spacing: 8) {
                                Text("THE CORE").font(.system(size: 11, weight: .semibold)).foregroundStyle(Theme.text)
                                line("Address", session.address.map { "\($0.host):\($0.port)" } ?? "—")
                                line("Paired as", session.deviceName ?? "—")
                                line("Core version", session.metrics?.coreVersion ?? "—")
                                line("Scope", session.info?.scope ?? "—")
                            }
                        }
                        Panel(marked: false) {
                            Toggle(isOn: $session.speakReplies) {
                                VStack(alignment: .leading, spacing: 2) {
                                    Text("Speak replies").font(.system(size: 13, weight: .semibold)).foregroundStyle(Theme.text)
                                    Text("The reply is spoken in JARVIS's voice, made on the PC, when the owner allows this phone's speakers.")
                                        .font(.system(size: 10)).foregroundStyle(Theme.muted)
                                }
                            }
                            .tint(Theme.accent)
                        }
                        Panel(marked: false) {
                            VStack(alignment: .leading, spacing: 8) {
                                Toggle(isOn: $session.lockEnabled) {
                                    VStack(alignment: .leading, spacing: 2) {
                                        Text("Lock with Face ID").font(.system(size: 13, weight: .semibold)).foregroundStyle(Theme.text)
                                        Text("Face ID, or the phone's passcode, before the screens show: at every open and after a minute away. STOP ALL works on the lock screen without unlocking.")
                                            .font(.system(size: 10)).foregroundStyle(Theme.muted)
                                    }
                                }
                                .tint(Theme.accent)
                                Text("Turn this on only once the Face ID entry is in the Xcode project (the round-2 README says how). Without it iOS ends the app at the first prompt.")
                                    .font(.system(size: 10)).foregroundStyle(Theme.warn.opacity(0.9))
                            }
                        }
                        Panel(marked: false) {
                            VStack(alignment: .leading, spacing: 8) {
                                Text("THIS PAIRING").font(.system(size: 11, weight: .semibold)).foregroundStyle(Theme.text)
                                Text("Forgetting removes the key from this phone. The PC still lists the device until the owner removes it there; pairing again gives a new key.")
                                    .font(.system(size: 10)).foregroundStyle(Theme.muted)
                                Button(role: .destructive) { confirmForget = true } label: {
                                    Text("FORGET THIS PAIRING").font(Theme.caption(10)).tracking(1.2).foregroundStyle(Theme.bad)
                                        .frame(maxWidth: .infinity).frame(height: 38)
                                        .overlay(Rectangle().stroke(Theme.bad.opacity(0.6), lineWidth: 1))
                                }
                            }
                        }
                        Panel(marked: false) {
                            VStack(alignment: .leading, spacing: 6) {
                                Text("ABOUT").font(.system(size: 11, weight: .semibold)).foregroundStyle(Theme.text)
                                Text("JARVIS for iPhone, version \(AppInfo.version). One Core, one JARVIS: this phone is a client of the Core on the owner's PC over the owner's private network. The emergency stop can be raised here, from Siri (\"Hey Siri, stop JARVIS\") and from the lock screen, and lifted only on the PC. \"Hey Siri, ask JARVIS\" opens the app with your question.")
                                    .font(.system(size: 10)).foregroundStyle(Theme.muted)
                            }
                        }
                    }
                    .padding(16)
                }
            }
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) { Button("Done") { dismiss() }.tint(Theme.accent) }
            }
            .toolbarBackground(Theme.ground2, for: .navigationBar)
            .navigationTitle("Phone settings")
            .navigationBarTitleDisplayMode(.inline)
        }
        .alert("Forget this pairing?", isPresented: $confirmForget) {
            Button("Forget", role: .destructive) { session.forgetPairing(); dismiss() }
            Button("Cancel", role: .cancel) {}
        } message: { Text("The key is removed from this phone. To use JARVIS again, pair with a new code from the PC.") }
    }

    private func line(_ label: String, _ value: String) -> some View {
        HStack(alignment: .firstTextBaseline, spacing: 8) {
            Caption(label, size: 8).frame(width: 90, alignment: .leading)
            Text(value).font(.system(size: 11)).foregroundStyle(Theme.text)
            Spacer()
        }
    }
}
