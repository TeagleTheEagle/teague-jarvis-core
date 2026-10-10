import SwiftUI

/// The sheet of Share to JARVIS: what was shared, the question with a few suggestions, SEND, and the reply; STOP ALL
/// at the top right, as on every screen of the app.
struct ShareSheet: View {
    @ObservedObject var model: ShareModel
    @State private var confirmStop = false

    var body: some View {
        NavigationStack {
            ZStack {
                PageBackground()
                switch model.phase {
                case .reading: reading
                case .locked: locked
                case .ready, .asking: main
                }
            }
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("Close") { model.finish() }.tint(Theme.accent)
                }
                ToolbarItem(placement: .topBarTrailing) {
                    StopButton(stopped: model.stopped) { confirmStop = true }
                        .disabled(!model.paired)
                }
            }
            .toolbarBackground(Theme.ground2, for: .navigationBar)
            .toolbarBackground(.visible, for: .navigationBar)
            .navigationTitle("Share to JARVIS")
            .navigationBarTitleDisplayMode(.inline)
            .alert("Stop everything on the PC?", isPresented: $confirmStop) {
                Button("STOP ALL", role: .destructive) { Task { await model.stopEverything() } }
                Button("Cancel", role: .cancel) {}
            } message: { Text("JARVIS stops until RESUME is pressed on the PC.") }
        }
        .preferredColorScheme(.dark)
        .tint(Theme.accent)
    }

    private var reading: some View {
        VStack(spacing: 12) {
            ProgressView().tint(Theme.accent)
            Caption("Reading what was shared", color: Theme.muted, size: 9)
        }
    }

    /// The app's lock, when the owner has turned it on: Face ID or the passcode before anything is shown or sent.
    private var locked: some View {
        VStack(spacing: 16) {
            Spacer()
            JarvisMark().frame(width: 64, height: 64)
            Caption("Locked", color: Theme.accent, size: 9)
            Button {
                Task { await model.unlock() }
            } label: {
                HStack(spacing: 8) {
                    Image(systemName: "faceid").font(.system(size: 16))
                    Text("UNLOCK").font(Theme.caption(12)).tracking(1.5)
                }
                .frame(maxWidth: .infinity).frame(height: 46)
                .background(Theme.accent)
                .foregroundStyle(Theme.ground2)
            }
            .padding(.horizontal, 48)
            Text("The emergency stop works without unlocking.").font(.system(size: 10)).foregroundStyle(Theme.muted)
            Spacer()
        }
        .padding(16)
    }

    private var main: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                if let item = model.item { SharedPreview(item: item) }
                ForEach(model.lines) { line in
                    bubble("You", line.asked, mine: true)
                    if let reply = line.reply { bubble("JARVIS", reply, mine: false) }
                }
                if model.phase == .asking { working }
                if model.stopped { warning(ShareModel.stopNote) }
                if model.needsCamera { warning(ShareModel.cameraNote) }
                if let note = model.note { warning(note) }
                if model.phase == .ready, model.paired, !model.stopped { askBox }
                Text("The question and the reply also stay in the JARVIS app, under Chats. What you send goes to your PC and, from there, to JARVIS's AI provider.")
                    .font(.system(size: 10)).foregroundStyle(Theme.muted)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .padding(16)
        }
        .scrollDismissesKeyboard(.interactively)
    }

    private var askBox: some View {
        VStack(alignment: .leading, spacing: 8) {
            Caption(model.lines.isEmpty ? "Ask JARVIS" : "Ask more about it", color: Theme.accent, size: 9)
            TextField(model.lines.isEmpty ? "What should JARVIS do with it?" : "A follow-up question",
                      text: $model.question, axis: .vertical)
                .font(.system(size: 14)).foregroundStyle(Theme.text)
                .lineLimit(1...5)
                .padding(12)
                .background(Theme.ground.opacity(0.7))
                .overlay(Rectangle().stroke(Theme.accent.opacity(0.3), lineWidth: 1))
            if model.lines.isEmpty, let item = model.item {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(item.suggestions, id: \.self) { words in
                            Button { model.question = words } label: {
                                Text(words).font(.system(size: 12)).foregroundStyle(Theme.accent)
                                    .padding(.horizontal, 12).frame(height: 32)
                                    .overlay(RoundedRectangle(cornerRadius: 16).stroke(Theme.accent.opacity(0.45), lineWidth: 1))
                                    .frame(minHeight: 44)
                                    .contentShape(Rectangle())
                            }
                        }
                    }
                }
            }
            Button(action: model.send) {
                HStack(spacing: 8) {
                    Image(systemName: "paperplane.fill").font(.system(size: 14))
                    Text("SEND TO JARVIS").font(Theme.caption(11)).tracking(1.4)
                }
                .foregroundStyle(Theme.ground2)
                .frame(maxWidth: .infinity).frame(height: 46)
                .background(model.maySend ? Theme.accent : Theme.muted)
            }
            .disabled(!model.maySend)
        }
    }

    /// While the Core works: what it is doing, and the reply as it is being written when the PC sends it.
    private var working: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 8) {
                ProgressView().tint(Theme.accent)
                Caption(model.tool.map { "Working: \($0)" } ?? (model.writing == nil ? "Thinking" : "Writing"),
                        color: Theme.accent, size: 9)
            }
            if let writing = model.writing {
                Text(writing).font(.system(size: 13)).foregroundStyle(Theme.text.opacity(0.8))
                    .padding(10)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .overlay(Rectangle().stroke(Theme.accent.opacity(0.5), style: StrokeStyle(lineWidth: 1, dash: [4, 3])))
            }
        }
    }

    private func warning(_ text: String) -> some View {
        Text(text).font(.system(size: 12)).foregroundStyle(Theme.warn)
            .fixedSize(horizontal: false, vertical: true)
    }

    private func bubble(_ who: String, _ text: String, mine: Bool) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Caption(who, color: mine ? Theme.muted : Theme.accent, size: 9)
            Text(text).font(.system(size: 14)).foregroundStyle(Theme.text)
                .textSelection(.enabled)
                .fixedSize(horizontal: false, vertical: true)
        }
        .padding(12)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Theme.ground.opacity(mine ? 0.5 : 0.85))
        .overlay(Rectangle().stroke((mine ? Theme.muted : Theme.accent).opacity(0.35), lineWidth: 1))
    }
}

/// What was shared, as it goes with the first question.
struct SharedPreview: View {
    let item: SharedItem

    var body: some View {
        Panel {
            VStack(alignment: .leading, spacing: 6) {
                Caption(kind, color: Theme.accent, size: 9)
                switch item {
                case .picture(_, let preview):
                    Image(uiImage: preview).resizable().scaledToFit()
                        .frame(maxHeight: 220)
                        .accessibilityLabel("The shared picture")
                case .unusablePicture:
                    line("A picture that could not be read.")
                case .page(let title, let address, let selection, let text):
                    if !title.isEmpty {
                        Text(title).font(.system(size: 14, weight: .semibold)).foregroundStyle(Theme.text).lineLimit(3)
                    }
                    if let host = URL(string: address)?.host { line(host) }
                    line(pageLine(text, selection: selection))
                    if !selection.isEmpty { line("Selected: \(selection)").lineLimit(3) }
                case .link(let address, let title):
                    if let title, !title.isEmpty, title != address {
                        Text(title).font(.system(size: 14, weight: .semibold)).foregroundStyle(Theme.text).lineLimit(3)
                    }
                    line(address).lineLimit(2)
                case .text(let words):
                    Text(words).font(.system(size: 13)).foregroundStyle(Theme.text).lineLimit(6)
                }
            }
        }
    }

    private var kind: String {
        switch item {
        case .page: return "Web page"
        case .link: return "Link"
        case .text: return "Text"
        case .picture, .unusablePicture: return "Picture"
        }
    }

    private func line(_ text: String) -> Text {
        Text(text).font(.system(size: 11)).foregroundStyle(Theme.muted)
    }

    /// What of the page goes with the question. The selected words go first and use the room first; then the page's
    /// text, all of it or its first part (ShareQuestion cuts it to fit with the question's words).
    private func pageLine(_ text: String, selection: String) -> String {
        let chosen = selection.unicodeScalars.count
        let room = max(0, ShareQuestion.pageRoom - chosen)
        let size = text.unicodeScalars.count
        switch (chosen > 0, text.isEmpty) {
        case (false, true):
            return "The page's address goes with your question."
        case (true, true):
            return "The selected words go with your question."
        case (true, false) where room < 200:
            return "The selected words go with your question; the page's text does not fit beside them."
        case (false, false) where size <= room:
            return "The page's text (\(size.formatted()) characters) goes with your question."
        case (false, false):
            return "The first \(room.formatted()) or so of the page's \(size.formatted()) characters go with your question."
        case (true, false) where size <= room:
            return "The selected words and the page's text (\(size.formatted()) characters) go with your question."
        case (true, false):
            return "The selected words and the first \(room.formatted()) or so of the page's \(size.formatted()) characters go with your question."
        }
    }
}
