import SwiftUI

/// Screen 1 of the canvas: the Core, its state, hold to speak, type, and the conversation in progress.
struct AskView: View {
    @EnvironmentObject private var session: SessionModel
    @State private var typing = false
    @State private var showSettings = false
    @State private var confirmStop = false
    @FocusState private var fieldFocused: Bool

    var body: some View {
        ZStack {
            PageBackground()
            VStack(spacing: 8) {
                ScreenHeader(subtitle: "One Core // Private network") {
                    HStack(spacing: 8) {
                        HStack(spacing: 6) {
                            StatusDot(color: dotColor)
                            Caption(dotText, color: Theme.text, size: 9)
                        }
                        StopButton(stopped: session.stopped) { confirmStop = true }
                        IconButton(system: "line.3.horizontal", label: "Phone settings") { showSettings = true }
                    }
                }
                ScrollView {
                    VStack(spacing: 10) {
                        ZStack {
                            CoreRing(state: session.state, recordingSeconds: session.recordingSeconds)
                                .frame(height: 300)
                            readouts
                        }
                        .padding(.top, 4)
                        VStack(spacing: 4) {
                            Text(stateLabel).font(.system(size: 17, weight: .medium)).foregroundStyle(Theme.text)
                            Text(hint).font(.system(size: 11)).foregroundStyle(Theme.muted)
                                .multilineTextAlignment(.center)
                        }
                        if let notice = session.notice {
                            Text(notice).font(.system(size: 11)).foregroundStyle(noticeColor)
                                .multilineTextAlignment(.center).padding(.horizontal, 12)
                        }
                        transcript
                    }
                }
                .scrollIndicators(.hidden)
                if typing { typeBar }
                controls
            }
            .padding(.horizontal, 16)
            .padding(.bottom, 8)
        }
        .sheet(isPresented: $showSettings) { SettingsSheet() }
        .alert("Stop everything on the PC?", isPresented: $confirmStop) {
            Button("STOP ALL", role: .destructive) { Task { await session.stopEverything() } }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("JARVIS stops answering and doing anything until RESUME is pressed on the PC. The phone cannot resume.")
        }
        .onAppear {
            session.prepareMicrophone()
            session.startHealthPolling()   // the readouts around the Core, read every 5 seconds while this screen shows
        }
        .onDisappear { session.stopHealthPolling() }
    }

    // MARK: pieces

    private var readouts: some View {
        VStack {
            HStack {
                readout("Core", value: session.metrics?.coreVersion ?? "—", leading: true)
                readout("AI", value: aiText, leading: true)
                Spacer()
                readout("CPU", value: percent(session.metrics?.cpuPercent), leading: false)
                readout("Link", value: session.roundTripMs.map { "\($0) ms" } ?? "—", leading: false)
            }
            Spacer()
            HStack {
                readout("Memory", value: percent(session.metrics?.memory?.usedPercent), leading: true)
                Spacer()
                readout("Stop", value: session.stopped ? "ON" : "CLEAR", leading: false)
            }
        }
        .padding(.horizontal, 4)
        .padding(.vertical, 20)
        .allowsHitTesting(false)
    }

    private func readout(_ label: String, value: String, leading: Bool) -> some View {
        VStack(alignment: leading ? .leading : .trailing, spacing: 2) {
            Caption(label, size: 8)
            Text(value).font(.system(size: 12, weight: .light)).foregroundStyle(Theme.text).lineLimit(1)
        }
        .padding(.horizontal, 8)
        .overlay(alignment: leading ? .leading : .trailing) {
            Rectangle().fill(Theme.accent.opacity(0.35)).frame(width: 1)
        }
    }

    private var transcript: some View {
        VStack(spacing: 8) {
            ForEach(session.lines.suffix(6)) { line in
                HStack {
                    if line.isUser { Spacer(minLength: 40) }
                    Text(line.text)
                        .font(.system(size: 14))
                        .foregroundStyle(Theme.text)
                        .padding(10)
                        .background(line.isUser ? Theme.accent.opacity(0.14) : Theme.ground.opacity(0.8))
                        .overlay(Rectangle().stroke(line.isUser ? Theme.accent.opacity(0.5) : Theme.accent.opacity(0.2), lineWidth: 1))
                        .frame(maxWidth: .infinity, alignment: line.isUser ? .trailing : .leading)
                        .textSelection(.enabled)
                    if !line.isUser { Spacer(minLength: 40) }
                }
            }
            if session.lines.count > 6 {
                Caption("Earlier lines are in Chats", size: 8)
            }
        }
        .padding(.top, 6)
    }

    private var typeBar: some View {
        HStack(spacing: 8) {
            TextField("Ask JARVIS anything…", text: $session.draft)
                .font(.system(size: 14))
                .foregroundStyle(Theme.text)
                .focused($fieldFocused)
                .submitLabel(.send)
                .onSubmit { session.send() }
                .padding(.horizontal, 12).frame(minHeight: 40)
                .background(Theme.ground.opacity(0.7))
                .overlay(Rectangle().stroke(Theme.accent.opacity(0.3), lineWidth: 1))
            Button { session.send(); fieldFocused = true } label: {
                Image(systemName: "paperplane.fill").font(.system(size: 16)).foregroundStyle(Theme.accent)
                    .frame(width: 40, height: 40)
                    .overlay(Rectangle().stroke(Theme.accent.opacity(0.3), lineWidth: 1))
            }
            .accessibilityLabel("Send")
            .disabled(session.busy || session.draft.trimmingCharacters(in: .whitespaces).isEmpty)
        }
    }

    private var controls: some View {
        HStack(alignment: .top, spacing: 22) {
            VStack(spacing: 6) {
                Button {
                    typing.toggle()
                    fieldFocused = typing
                } label: {
                    roundButton("keyboard", tint: Theme.accent)
                }
                .accessibilityLabel("Type a request")
                Caption("Type", size: 8)
            }
            VStack(spacing: 6) {
                HoldToSpeakButton()
                Caption("Microphone", color: Theme.accent, size: 8)
            }
            VStack(spacing: 6) {
                // Speak replies, on the screen itself (the settings sheet has the same switch): the reply is spoken
                // in JARVIS's voice when on and the owner allows this phone's speakers; the text shows either way.
                Button {
                    session.speakReplies.toggle()
                } label: {
                    roundButton(session.speakReplies ? "speaker.wave.2.fill" : "speaker.slash.fill", tint: session.speakReplies ? Theme.accent : Theme.muted)
                }
                .accessibilityLabel(session.speakReplies ? "Replies are spoken. Tap to mute them" : "Replies are silent. Tap to speak them")
                Caption(session.speakReplies ? "Voice on" : "Muted", color: session.speakReplies ? Theme.accent : Theme.muted, size: 8)
            }
            VStack(spacing: 6) {
                Button {
                    if session.busy { session.interrupt() } else { session.newConversation() }
                } label: {
                    roundButton(session.busy ? "xmark" : "plus.bubble", tint: Theme.accent)
                }
                .accessibilityLabel(session.busy ? "Cancel this question" : "New conversation")
                Caption(session.busy ? "Cancel" : "New chat", size: 8)
            }
        }
        .padding(.top, 6)
    }

    /// The 52 pt round buttons beside the microphone (four of them fit a 393 pt phone with room to spare).
    private func roundButton(_ system: String, tint: Color) -> some View {
        Image(systemName: system).font(.system(size: 18)).foregroundStyle(tint)
            .frame(width: 52, height: 52)
            .background(RadialGradient(colors: [Color(hex: 0x0B2A44), Theme.ground], center: .init(x: 0.5, y: 0.4), startRadius: 2, endRadius: 40))
            .clipShape(Circle())
            .overlay(Circle().stroke(tint.opacity(0.35), lineWidth: 1))
    }

    // MARK: words

    private var dotColor: Color {
        switch session.state {
        case .offline: return Theme.muted
        case .stopped, .error: return Theme.bad
        default: return Theme.good
        }
    }
    private var dotText: String {
        switch session.state {
        case .offline: return "Not reached"
        case .stopped: return "Stopped"
        default: return "Online"
        }
    }
    private var aiText: String {
        guard let m = session.metrics else { return "—" }
        return m.aiReady ? "READY" : "NO KEY"
    }
    private func percent(_ value: Double?) -> String { value.map { "\(Int($0.rounded()))%" } ?? "—" }

    private var stateLabel: String {
        switch session.state {
        case .offline: return "CORE NOT REACHED"
        case .idle: return "STANDING BY"
        case .listening: return "LISTENING"
        case .thinking: return "THINKING"
        case .executing: return "WORKING"
        case .speaking: return "SPEAKING"
        case .stopped: return "EMERGENCY STOP"
        case .error: return "NOT ANSWERED"
        }
    }
    private var hint: String {
        switch session.state {
        case .offline: return "Tailscale on, on the PC and here? The Private network switch on in Settings > Devices?"
        case .idle: return "Hold the microphone and speak, or type."
        case .listening: return String(format: "Release to send · %.0f s of 30", session.recordingSeconds)
        case .thinking: return "On the PC."
        case .executing: return session.toolName.map { "Using \($0.replacingOccurrences(of: "_", with: " "))." } ?? "Using a tool on the PC."
        case .speaking: return "In JARVIS's voice."
        case .stopped: return "Press RESUME on the PC to continue."
        case .error: return "See the line below."
        }
    }
    private var noticeColor: Color {
        switch session.state {
        case .error, .stopped, .offline: return Theme.warn
        default: return Theme.muted
        }
    }
}

/// Hold to speak: the recording starts on touch and is sent when the finger lifts (at most 30 seconds).
struct HoldToSpeakButton: View {
    @EnvironmentObject private var session: SessionModel
    @State private var pressing = false

    var body: some View {
        ZStack {
            Circle().stroke(Theme.accent.opacity(session.recording ? 0.9 : 0.35), lineWidth: 1).frame(width: 84, height: 84)
                .scaleEffect(session.recording ? 1.06 : 1)
                .animation(session.recording ? .easeInOut(duration: 0.6).repeatForever(autoreverses: true) : .default, value: session.recording)
            Circle()
                .fill(RadialGradient(colors: [Color(hex: 0x0F3F66), Theme.ground], center: .init(x: 0.5, y: 0.35), startRadius: 2, endRadius: 46))
                .frame(width: 56, height: 56)
                .overlay(Circle().stroke(session.recording ? Theme.bad : Theme.accent, lineWidth: 1))
            Image(systemName: session.recording ? "waveform" : "mic.fill").font(.system(size: 20)).foregroundStyle(Theme.text)
        }
        .frame(width: 84, height: 84)
        .contentShape(Circle())
        .gesture(DragGesture(minimumDistance: 0)
            .onChanged { _ in
                if !pressing {
                    pressing = true
                    session.holdToSpeakBegan()
                }
            }
            .onEnded { _ in
                pressing = false
                session.holdToSpeakEnded()
            })
        .accessibilityLabel("Hold to speak")
        .accessibilityHint("Hold, speak, and release to send")
        .accessibilityAction(named: "Start or stop recording") { session.toggleRecording() }   // VoiceOver cannot hold
    }
}

/// The Core on the Ask screen: rings that turn with the state. Cyan standing by, green while listening, amber
/// while thinking or working, red when stopped; still when the Core is not reached.
struct CoreRing: View {
    let state: JarvisState
    let recordingSeconds: Double

    private var color: Color {
        switch state {
        case .offline: return Theme.muted
        case .listening: return Theme.good
        case .thinking, .executing: return Theme.warn
        case .stopped, .error: return Theme.bad
        default: return Theme.accent
        }
    }
    private var speed: Double {
        switch state {
        case .offline, .stopped: return 0
        case .thinking, .executing: return 2.2
        case .listening, .speaking: return 1.3
        default: return 0.5
        }
    }

    var body: some View {
        TimelineView(.animation(minimumInterval: 1.0 / 30, paused: speed == 0)) { context in
            let t = context.date.timeIntervalSinceReferenceDate * speed
            ZStack {
                Circle().stroke(color.opacity(0.15), lineWidth: 1)
                Circle().stroke(color.opacity(0.25), lineWidth: 1).padding(22)
                Circle().stroke(color.opacity(0.35), lineWidth: 1).padding(48)
                Circle().trim(from: 0, to: 0.28).stroke(color, style: StrokeStyle(lineWidth: 3, lineCap: .round))
                    .padding(10).rotationEffect(.degrees(t * 40))
                Circle().trim(from: 0, to: 0.18).stroke(color.opacity(0.8), style: StrokeStyle(lineWidth: 2, lineCap: .round))
                    .padding(10).rotationEffect(.degrees(-t * 40 + 140))
                Circle().trim(from: 0, to: 0.42).stroke(color.opacity(0.6), style: StrokeStyle(lineWidth: 2, lineCap: .round))
                    .padding(32).rotationEffect(.degrees(-t * 25))
                Circle()
                    .fill(RadialGradient(colors: [color.opacity(0.45), Theme.ground.opacity(0.1)], center: .center, startRadius: 4, endRadius: 80))
                    .padding(60)
                if state == .listening {
                    Circle().stroke(Theme.good.opacity(0.6), lineWidth: 1)
                        .padding(60 - min(28, recordingSeconds * 2))
                }
            }
        }
        .aspectRatio(1, contentMode: .fit)
        .accessibilityHidden(true)
    }
}
