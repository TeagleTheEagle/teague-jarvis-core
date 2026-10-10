import PhotosUI
import SwiftUI
import UIKit

/// Screen 1 of the canvas: the Core, its state, the microphone (a tap for a conversation, a hold for one question),
/// type, quick asks, a picture to ask about, and the conversation in progress. The look follows the owner's picture
/// of 2026-10-10: readout plates around the orb and the Earth's horizon under it (round 6).
struct AskView: View {
    @EnvironmentObject private var session: SessionModel
    @State private var typing = false
    @State private var showSettings = false
    @State private var showApprovals = false
    @State private var showNotices = false
    @State private var confirmStop = false
    @State private var chooseLook = false
    @State private var showPhotos = false
    @State private var showCamera = false
    @State private var photoItem: PhotosPickerItem?
    @State private var picked: PickedPhoto?
    @State private var cameraShot: UIImage?
    @FocusState private var fieldFocused: Bool

    var body: some View {
        ZStack {
            PageBackground()
            EarthBand()
            VStack(spacing: 8) {
                ScreenHeader(subtitle: "One Core // Private network") {
                    HStack(spacing: 8) {
                        HeaderState(state: session.state)
                        StopButton(stopped: session.stopped) { confirmStop = true }
                        IconButton(system: "line.3.horizontal", label: "Phone settings") { showSettings = true }
                    }
                }
                ScrollView {
                    VStack(spacing: 10) {
                        core
                        VStack(spacing: 4) {
                            Text(stateLabel).font(.system(size: 20, weight: .semibold)).foregroundStyle(Theme.text)
                            Text(hint).font(.system(size: 12)).foregroundStyle(Theme.text.opacity(0.8))
                                .multilineTextAlignment(.center)
                        }
                        if session.conversing { conversationBar }
                        if let notice = session.notice {
                            Text(notice).font(.system(size: 11)).foregroundStyle(noticeColor)
                                .multilineTextAlignment(.center).padding(.horizontal, 12)
                        }
                        if session.waitingApprovals > 0 {
                            // Core 1.0.17, R2: something waits for the owner's word on the PC; the panel opens from here.
                            Button { showApprovals = true } label: {
                                HStack(spacing: 8) {
                                    Image(systemName: "checkmark.seal").font(.system(size: 12))
                                    Text(session.waitingApprovals == 1 ? "1 approval waiting · open" : "\(session.waitingApprovals) approvals waiting · open")
                                        .font(.system(size: 11, weight: .semibold))
                                }
                                .foregroundStyle(Theme.warn)
                                .frame(minHeight: 44)
                                .contentShape(Rectangle())
                            }
                            .accessibilityLabel("Open approvals")
                        }
                        transcript
                    }
                }
                .scrollIndicators(.hidden)
                if typing { typeBar }
                quickAsks
                controls
            }
            .padding(.horizontal, 16)
            .padding(.bottom, 8)
        }
        .sheet(isPresented: $showSettings) { SettingsSheet() }
        .sheet(isPresented: $showApprovals) { ApprovalsView() }
        .sheet(isPresented: $showNotices) { NoticesView() }
        .sheet(item: $picked) { photo in PhotoQuestionSheet(photo: photo) }
        .confirmationDialog("Look at this", isPresented: $chooseLook, titleVisibility: .visible) {
            if UIImagePickerController.isSourceTypeAvailable(.camera) {
                Button("Take a photo") { showCamera = true }
            }
            Button("Choose from Photos") { showPhotos = true }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("Ask JARVIS about a picture. It goes to your PC, and from there to JARVIS's AI provider.")
        }
        .photosPicker(isPresented: $showPhotos, selection: $photoItem, matching: .images)
        .onChange(of: photoItem) { _, item in
            guard let item else { return }
            Task {
                if let data = try? await item.loadTransferable(type: Data.self),
                   // A copy to show, read at screen size away from the screen's thread; the file's bytes stay for SEND.
                   let preview = await Task.detached(priority: .userInitiated, operation: {
                       PhotoPrep.preview(fromImageData: data, longest: 1200)
                   }).value {
                    picked = PickedPhoto(preview: preview, source: .file(data))
                } else {
                    session.pictureNotRead()
                }
                photoItem = nil
            }
        }
        .fullScreenCover(isPresented: $showCamera, onDismiss: {
            // The question sheet opens once the camera has gone: two presentations in one update may drop one.
            if let shot = cameraShot { picked = PickedPhoto(preview: shot, source: .camera(shot)) }
            cameraShot = nil
        }) {
            CameraPicker { image in
                cameraShot = image
                showCamera = false
            }
            .ignoresSafeArea()
        }
        .alert("Stop everything on the PC?", isPresented: $confirmStop) {
            Button("STOP ALL", role: .destructive) { Task { await session.stopEverything() } }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("JARVIS stops answering and doing anything until RESUME is pressed on the PC. The phone cannot resume.")
        }
        .onAppear { session.prepareMicrophone() }   // the health polling for the readouts is owned by MainTabs
    }

    // MARK: pieces

    /// The orb between its readout plates: CORE and AI, CPU and LINK above it; MEMORY and STOP at its lower corners.
    private var core: some View {
        VStack(spacing: 0) {
            HStack(alignment: .top, spacing: 8) {
                // The short readouts keep their room; the long release id shrinks to fit (seen on the phone: with
                // the priority the other way round, LINK read "33…").
                HudPlate(items: [("Core", session.metrics?.coreVersion ?? "—"), ("AI", aiText)])
                Spacer(minLength: 0)
                HudPlate(items: [("CPU", percent(session.metrics?.cpuPercent)),
                                 ("Link", session.roundTripMs.map { "\($0) ms" } ?? "—")], mirrored: true)
                    .layoutPriority(1)
            }
            ZStack(alignment: .bottom) {
                CoreOrb(state: session.state, level: session.micLevels.last ?? 0)
                    .frame(height: 280)
                HStack(alignment: .bottom) {
                    HudPlate(items: [("Memory", percent(session.metrics?.memory?.usedPercent))])
                    Spacer()
                    HudPlate(items: [("Stop", session.stopped ? "ON" : "CLEAR")], mirrored: true)
                }
            }
            .padding(.top, 2)
        }
        .padding(.top, 4)
        .allowsHitTesting(false)
    }

    /// Round 6: the conversation is on, and how to end it.
    private var conversationBar: some View {
        HStack(spacing: 10) {
            StatusDot(color: Theme.good)
            VStack(alignment: .leading, spacing: 2) {
                Caption("Conversation on", color: Theme.good, size: 9)
                Text("Say \"thank you Jarvis\" or tap the microphone to end.")
                    .font(.system(size: 11)).foregroundStyle(Theme.muted)
            }
            Spacer(minLength: 6)
            Button { session.endConversation(saying: "Conversation ended.") } label: {
                Text("END").font(Theme.caption(10)).tracking(1.2).foregroundStyle(Theme.good)
                    .padding(.horizontal, 14).frame(height: 30)
                    .overlay(RoundedRectangle(cornerRadius: 6).stroke(Theme.good.opacity(0.7), lineWidth: 1))
                    .frame(minHeight: 44)
                    .contentShape(Rectangle())
            }
            .accessibilityLabel("End the conversation")
        }
        .padding(.horizontal, 12)
        .background(Theme.ground.opacity(0.7))
        .overlay(Rectangle().stroke(Theme.good.opacity(0.4), lineWidth: 1))
    }

    private var transcript: some View {
        VStack(spacing: 8) {
            ForEach(session.lines.suffix(6)) { line in
                HStack {
                    if line.isUser { Spacer(minLength: 40) }
                    VStack(alignment: line.isUser ? .trailing : .leading, spacing: 6) {
                        if let photo = line.photo, let image = UIImage(data: photo) {
                            Image(uiImage: image).resizable().scaledToFit()
                                .frame(maxWidth: 150, maxHeight: 150)
                                .accessibilityLabel("The picture you sent")
                        }
                        Text(line.text)
                            .font(.system(size: 14))
                            .foregroundStyle(Theme.text)
                    }
                    .padding(10)
                    .background(line.isUser ? Theme.accent.opacity(0.14) : Theme.ground.opacity(0.85))
                    .overlay(Rectangle().stroke(line.isUser ? Theme.accent.opacity(0.5) : Theme.accent.opacity(0.2), lineWidth: 1))
                    .frame(maxWidth: .infinity, alignment: line.isUser ? .trailing : .leading)
                    .contentShape(Rectangle())
                    // Round 6: a tap on a reply reads it again; a press and hold copies or shares a line.
                    .onTapGesture { if !line.isUser { session.hearAgain(line.text) } }
                    .contextMenu {
                        if !line.isUser {
                            Button { session.hearAgain(line.text) } label: { Label("Hear again", systemImage: "speaker.wave.2") }
                        }
                        Button { UIPasteboard.general.string = line.text } label: { Label("Copy", systemImage: "doc.on.doc") }
                        ShareLink(item: line.text) { Label("Share", systemImage: "square.and.arrow.up") }
                    }
                    .accessibilityHint(line.isUser ? "" : "Double tap to hear it again")
                    if !line.isUser { Spacer(minLength: 40) }
                }
            }
            if let writing = session.writing {
                // The reply as the PC writes it (Core 1.0.17): the whole text so far, replaced at each step, never
                // spoken; the finished line takes its place.
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(writing)
                            .font(.system(size: 14))
                            .foregroundStyle(Theme.text.opacity(0.85))
                        Caption("Writing…", color: Theme.accent, size: 9)
                    }
                    .padding(10)
                    .background(Theme.ground.opacity(0.6))
                    .overlay(Rectangle().stroke(Theme.accent.opacity(0.35), style: StrokeStyle(lineWidth: 1, dash: [4, 3])))
                    .frame(maxWidth: .infinity, alignment: .leading)
                    Spacer(minLength: 40)
                }
                .accessibilityElement(children: .combine)
                .accessibilityLabel("JARVIS is writing: \(writing)")
            }
            if let held = session.held {
                // Hold-and-send: the question waits on the phone for the link; the owner may drop it.
                HStack(alignment: .center, spacing: 10) {
                    VStack(alignment: .leading, spacing: 4) {
                        Caption("Held until the Core is back", color: Theme.warn, size: 9)
                        Text(held.shown).font(.system(size: 12)).foregroundStyle(Theme.text.opacity(0.85)).lineLimit(2)
                    }
                    Spacer(minLength: 8)
                    Button { session.dropHeld() } label: {
                        Text("DROP").font(Theme.caption(9)).tracking(1.2).foregroundStyle(Theme.warn)
                            .padding(.horizontal, 10).frame(height: 30)
                            .overlay(RoundedRectangle(cornerRadius: 6).stroke(Theme.warn.opacity(0.7), lineWidth: 1))
                            .frame(minHeight: 44)   // the touch target
                            .contentShape(Rectangle())
                    }
                    .accessibilityLabel("Drop the held question")
                }
                .padding(10)
                .background(Theme.ground.opacity(0.6))
                .overlay(Rectangle().stroke(Theme.warn.opacity(0.45), style: StrokeStyle(lineWidth: 1, dash: [4, 3])))
            }
            if session.lines.count > 6 {
                Caption("Earlier lines are in Chats", size: 9)
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
                    .frame(width: 44, height: 44)
                    .overlay(Rectangle().stroke(Theme.accent.opacity(0.3), lineWidth: 1))
            }
            .accessibilityLabel("Send")
            .disabled(session.busy || session.held != nil || session.draft.trimmingCharacters(in: .whitespaces).isEmpty)
        }
    }

    /// Round 6: one tap instead of typing. "Any notices?" opens the PC's notices list itself (real data, read at once).
    private var quickAsks: some View {
        ScrollView(.horizontal) {
            HStack(spacing: 8) {
                chip("Look at this", system: "camera") { chooseLook = true }
                chip("What's on today?") { session.quickAsk("What's on today?") }
                chip("Analyse my screen") { session.quickAsk("Analyse my screen.") }
                chip("Any notices?", system: "bell") { showNotices = true }
                chip("How's the PC?") { session.quickAsk("How's the PC doing?") }
            }
            .padding(.horizontal, 1)
        }
        .scrollIndicators(.hidden)
    }

    private func chip(_ title: String, system: String? = nil, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack(spacing: 6) {
                if let system { Image(systemName: system).font(.system(size: 12)) }
                Text(title).font(.system(size: 12, weight: .medium))
            }
            .foregroundStyle(Theme.accent)
            .padding(.horizontal, 12).frame(height: 32)
            .background(Capsule().fill(Theme.ground.opacity(0.8)))
            .overlay(Capsule().stroke(Theme.accent.opacity(0.45), lineWidth: 1))
            .frame(minHeight: 44)   // the touch target
            .contentShape(Rectangle())
        }
        .disabled(session.recording)
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
                Caption("Type", size: 9)
            }
            VStack(spacing: 6) {
                HoldToSpeakButton()
                Caption(session.conversing ? "End" : "Microphone", color: session.conversing ? Theme.good : Theme.accent, size: 9)
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
                Caption(session.speakReplies ? "Voice on" : "Muted", color: session.speakReplies ? Theme.accent : Theme.muted, size: 9)
            }
            VStack(spacing: 6) {
                Button {
                    if session.busy { session.interrupt() } else { session.newConversation() }
                } label: {
                    roundButton(session.busy ? "xmark" : "plus.bubble", tint: Theme.accent)
                }
                .accessibilityLabel(session.busy ? "Cancel this question" : "New conversation")
                Caption(session.busy ? "Cancel" : "New chat", size: 9)
            }
        }
        .padding(.top, 2)
    }

    /// The 52 pt round buttons beside the microphone (four of them fit a 393 pt phone with room to spare).
    private func roundButton(_ system: String, tint: Color) -> some View {
        Image(systemName: system).font(.system(size: 18)).foregroundStyle(tint)
            .frame(width: 52, height: 52)
            .background(RadialGradient(colors: [Color(hex: 0x0B2A44), Theme.ground], center: .init(x: 0.5, y: 0.4), startRadius: 2, endRadius: 40))
            .clipShape(Circle())
            .overlay(Circle().stroke(tint.opacity(0.5), lineWidth: 1))
            .shadow(color: tint.opacity(0.3), radius: 4)
    }

    // MARK: words

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
        case .idle: return "Tap the microphone to talk, hold it for one question, or type."
        case .listening:
            if session.conversing { return String(format: "Your turn: speak, a pause sends · %.0f s of 30", session.recordingSeconds) }
            return session.handsFree
                ? String(format: "Speak; a pause sends, or tap the microphone · %.0f s of 30", session.recordingSeconds)
                : String(format: "Release to send · %.0f s of 30", session.recordingSeconds)
        case .thinking: return "On the PC."
        case .executing: return session.toolName.map { "Using \($0.replacingOccurrences(of: "_", with: " "))." } ?? "Using a tool on the PC."
        case .speaking: return session.conversing ? "In JARVIS's voice. Tap the microphone to skip to your turn." : "In JARVIS's voice."
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

/// The Earth's horizon under the orb (the owner's picture of 2026-10-10, cut from it): behind the screen's content,
/// above the quick asks and the buttons. Nothing is drawn when the image set is missing.
struct EarthBand: View {
    var body: some View {
        VStack(spacing: 0) {
            Spacer(minLength: 0)
            if UIImage(named: "EarthHorizon") != nil {
                // Laid over a box the screen's width: the picture itself (851 x 296) is 489 pt wide at 170 pt high,
                // and given its own width it widened the whole Ask screen past the phone's edges (seen on the phone
                // at 14:21 on 2026-10-10: the header and the plates cut off on both sides).
                Color.clear
                    .frame(height: 170)
                    .overlay(Image("EarthHorizon").resizable().scaledToFill())
                    .clipped()
                    .mask(LinearGradient(colors: [.clear, .black, .black, .black.opacity(0.6)], startPoint: .top, endPoint: .bottom))
            }
            Color.clear.frame(height: 196)   // the quick asks and the buttons below it
        }
        .ignoresSafeArea(.keyboard)
        .allowsHitTesting(false)
        .accessibilityHidden(true)
    }
}

/// The microphone: a tap starts a conversation (round 6), a hold records one question and sends it when the finger
/// lifts (at most 30 seconds). In a conversation a tap ends it, or, while JARVIS speaks, skips to the owner's turn.
struct HoldToSpeakButton: View {
    @EnvironmentObject private var session: SessionModel
    @State private var pressedAt: Date?
    /// True while a finger is on the button. SwiftUI resets it also when the system takes the touch away (a call, an
    /// alert), when no end of the press comes: then the press is put away, or the next press would be lost.
    @GestureState private var touching = false

    var body: some View {
        let ringColor = session.conversing ? Theme.good : Theme.accent
        ZStack {
            Circle().stroke(ringColor.opacity(session.recording ? 0.9 : 0.45), lineWidth: 1).frame(width: 84, height: 84)
                .scaleEffect(session.recording ? 1.06 : 1)
                .animation(session.recording ? .easeInOut(duration: 0.6).repeatForever(autoreverses: true) : .default, value: session.recording)
            Circle()
                .fill(RadialGradient(colors: [Color(hex: 0x0F3F66), Theme.ground], center: .init(x: 0.5, y: 0.35), startRadius: 2, endRadius: 46))
                .frame(width: 56, height: 56)
                .overlay(Circle().stroke(session.recording ? Theme.bad : ringColor, lineWidth: 1))
            Image(systemName: session.recording ? "waveform" : "mic.fill").font(.system(size: 20)).foregroundStyle(Theme.text)
        }
        .frame(width: 84, height: 84)
        .shadow(color: ringColor.opacity(0.35), radius: 6)
        .contentShape(Circle())
        .gesture(DragGesture(minimumDistance: 0)
            .updating($touching) { _, state, _ in state = true }
            .onChanged { _ in
                if pressedAt == nil {
                    pressedAt = Date()
                    session.microphonePressed()
                }
            }
            .onEnded { _ in
                let seconds = pressedAt.map { Date().timeIntervalSince($0) } ?? 1
                pressedAt = nil
                session.microphoneReleased(after: seconds)
            })
        .onChange(of: touching) { _, now in
            guard !now, let started = pressedAt else { return }
            // Looked at again a moment later, whichever order SwiftUI ends a press in: a press still open then (not
            // ended, no new one begun) was taken away by the system.
            Task { @MainActor in
                try? await Task.sleep(for: .milliseconds(300))
                guard pressedAt == started else { return }
                pressedAt = nil
                session.microphonePressCancelled()
            }
        }
        .accessibilityLabel("Microphone")
        .accessibilityHint(session.conversing ? "Tap to end the conversation" : "Tap to talk, or hold, speak and release for one question")
        .accessibilityAction(named: session.conversing ? "End the conversation" : "Start a conversation") {
            if session.conversing { session.endConversation(saying: "Conversation ended.") } else { session.requestHandsFree() }
        }
        .accessibilityAction(named: "Start or stop recording") { session.toggleRecording() }   // VoiceOver cannot hold
    }
}
