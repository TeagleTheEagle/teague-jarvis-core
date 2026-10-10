import SwiftUI

/// Screen 2 of the canvas: this phone's own conversations, as the Core keeps them. Never another device's and
/// never the PC's.
struct ChatsView: View {
    @EnvironmentObject private var session: SessionModel
    let showAsk: () -> Void
    @State private var conversations: [ConversationSummary] = []
    @State private var search = ""
    @State private var loading = false
    @State private var note: String?
    @State private var confirmStop = false

    private var shown: [ConversationSummary] {
        let needle = search.trimmingCharacters(in: .whitespaces).lowercased()
        guard !needle.isEmpty else { return conversations }
        return conversations.filter { ($0.title ?? "").lowercased().contains(needle) || ($0.last ?? "").lowercased().contains(needle) }
    }

    var body: some View {
        NavigationStack {
            ZStack {
                PageBackground()
                VStack(spacing: 8) {
                    ScreenHeader(subtitle: "Conversations") {
                        HStack(spacing: 6) {
                            StopButton(stopped: session.stopped) { confirmStop = true }
                            IconButton(system: "plus.bubble", label: "New conversation") {
                                session.newConversation()
                                showAsk()
                            }
                        }
                    }
                    Panel {
                        HStack(spacing: 12) {
                            VStack(alignment: .leading, spacing: 3) {
                                Text(session.overview.map { "\($0.conversations) CONVERSATIONS" } ?? "LATEST \(conversations.count)")
                                    .font(.system(size: 13, weight: .semibold)).foregroundStyle(Theme.text)
                                HStack(spacing: 6) {
                                    Caption(session.reached ? "From this phone" : "Core not reached", size: 8)
                                    StatusDot(color: session.reached ? Theme.good : Theme.muted)
                                }
                            }
                            Spacer()
                            if loading { ProgressView().tint(Theme.accent) }
                        }
                    }
                    HStack(spacing: 9) {
                        Image(systemName: "magnifyingglass").foregroundStyle(Theme.accent)
                        TextField("Search conversations…", text: $search)
                            .font(.system(size: 13)).foregroundStyle(Theme.text)
                            .textInputAutocapitalization(.never).autocorrectionDisabled()
                    }
                    .padding(.horizontal, 12).frame(height: 40)
                    .background(Theme.ground.opacity(0.7))
                    .overlay(Rectangle().stroke(Theme.accent.opacity(0.2), lineWidth: 1))
                    if let note {
                        Text(note).font(.system(size: 11)).foregroundStyle(Theme.warn).multilineTextAlignment(.center)
                    }
                    ScrollView {
                        LazyVStack(spacing: 7) {
                            ForEach(shown) { summary in
                                NavigationLink(value: summary.id) {
                                    ConversationRow(summary: summary, current: summary.id == session.conversation)
                                }
                                .buttonStyle(.plain)
                            }
                            if shown.isEmpty && !loading {
                                Text(conversations.isEmpty ? "No conversations from this phone yet. Ask something on the Ask screen." : "Nothing matches.")
                                    .font(.system(size: 12)).foregroundStyle(Theme.muted).padding(.top, 24)
                            }
                        }
                    }
                    .scrollIndicators(.hidden)
                    .refreshable { await load() }
                }
                .padding(.horizontal, 16)
            }
            .navigationDestination(for: String.self) { id in
                ConversationView(conversationId: id, summary: conversations.first { $0.id == id }, showAsk: showAsk)
            }
            .toolbar(.hidden, for: .navigationBar)
        }
        .task { await load() }
        .alert("Stop everything on the PC?", isPresented: $confirmStop) {
            Button("STOP ALL", role: .destructive) { Task { await session.stopEverything() } }
            Button("Cancel", role: .cancel) {}
        } message: { Text("JARVIS stops until RESUME is pressed on the PC.") }
    }

    private func load() async {
        loading = true
        defer { loading = false }
        do {
            conversations = try await session.client.conversations()
            note = nil
        } catch {
            note = session.report(error)   // a refused key sends the phone back to pairing, as everywhere
        }
    }
}

struct ConversationRow: View {
    let summary: ConversationSummary
    let current: Bool

    var body: some View {
        HStack(spacing: 12) {
            ZStack {
                Circle().fill(RadialGradient(colors: [Color(hex: 0x0B2A44), Theme.ground], center: .init(x: 0.5, y: 0.4), startRadius: 2, endRadius: 30))
                Circle().stroke(Theme.accent.opacity(current ? 0.8 : 0.35), lineWidth: 1)
                Image(systemName: "bubble.left").font(.system(size: 14)).foregroundStyle(Theme.accent)
            }
            .frame(width: 38, height: 38)
            VStack(alignment: .leading, spacing: 3) {
                HStack(spacing: 8) {
                    Text(summary.title?.isEmpty == false ? summary.title! : "Conversation")
                        .font(.system(size: 13.5, weight: .semibold)).foregroundStyle(Theme.text).lineLimit(1)
                    if current {
                        HStack(spacing: 4) { Circle().fill(Theme.good).frame(width: 4, height: 4); Text("ACTIVE") }
                            .font(Theme.caption(9)).foregroundStyle(Theme.good)
                            .padding(.horizontal, 6).frame(height: 16)
                            .overlay(RoundedRectangle(cornerRadius: 3).stroke(Theme.good.opacity(0.5), lineWidth: 1))
                    }
                }
                Text(summary.last ?? "").font(.system(size: 11.5)).foregroundStyle(Theme.accent).lineLimit(1)
                Text("\(summary.messages) messages").font(.system(size: 10)).foregroundStyle(Theme.muted)
            }
            Spacer(minLength: 6)
            VStack(spacing: 6) {
                Caption(Self.when(summary.updated), size: 8)
                Image(systemName: "chevron.right").font(.system(size: 10)).foregroundStyle(Theme.accent)
            }
        }
        .padding(.horizontal, 12).padding(.vertical, 10)
        .background(LinearGradient(colors: [current ? Color(hex: 0x0A2740).opacity(0.9) : Theme.ground.opacity(0.7), Color(hex: 0x040F1A).opacity(0.8)],
                                   startPoint: .top, endPoint: .bottom))
        .overlay(Rectangle().stroke(Theme.accent.opacity(current ? 0.7 : 0.2), lineWidth: 1))
    }

    /// TODAY, YESTERDAY, n DAYS, as the canvas labels them.
    static func when(_ seconds: Double) -> String {
        let date = Date(timeIntervalSince1970: seconds)
        let days = Calendar.current.dateComponents([.day], from: Calendar.current.startOfDay(for: date), to: Calendar.current.startOfDay(for: Date())).day ?? 0
        if days <= 0 { return "Today" }
        if days == 1 { return "Yesterday" }
        if days < 30 { return "\(days) days" }
        return date.formatted(.dateTime.day().month(.abbreviated))
    }
}

/// One conversation of this phone, read from the Core (`history`), continued on the Ask screen on request.
struct ConversationView: View {
    @EnvironmentObject private var session: SessionModel
    let conversationId: String
    let summary: ConversationSummary?
    let showAsk: () -> Void
    @State private var history: ConversationHistory?
    @State private var note: String?
    @State private var confirmStop = false

    var body: some View {
        ZStack {
            PageBackground()
            VStack(spacing: 8) {
                ScreenHeader(subtitle: "Conversation") {
                    HStack(spacing: 8) {
                        StopButton(stopped: session.stopped) { confirmStop = true }
                        Button {
                            if let history, let summary {
                                session.open(summary, history: history)
                                showAsk()
                            }
                        } label: {
                            Caption("Continue", color: Theme.accent, size: 9)
                                .padding(.horizontal, 10).frame(height: 30)
                                .overlay(RoundedRectangle(cornerRadius: 6).stroke(Theme.accent.opacity(0.5), lineWidth: 1))
                                .frame(minHeight: 44)
                                .contentShape(Rectangle())
                        }
                        .disabled(history == nil || summary == nil)
                    }
                }
                if let note {
                    Text(note).font(.system(size: 11)).foregroundStyle(Theme.warn).multilineTextAlignment(.center)
                }
                ScrollView {
                    LazyVStack(spacing: 8) {
                        ForEach(history?.messages ?? []) { message in
                            HStack {
                                if message.role == "user" { Spacer(minLength: 40) }
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(message.content).font(.system(size: 14)).foregroundStyle(Theme.text).textSelection(.enabled)
                                    Text(Date(timeIntervalSince1970: message.created).formatted(date: .abbreviated, time: .shortened))
                                        .font(.system(size: 9)).foregroundStyle(Theme.muted)
                                }
                                .padding(10)
                                .background(message.role == "user" ? Theme.accent.opacity(0.14) : Theme.ground.opacity(0.8))
                                .overlay(Rectangle().stroke(Theme.accent.opacity(message.role == "user" ? 0.5 : 0.2), lineWidth: 1))
                                if message.role != "user" { Spacer(minLength: 40) }
                            }
                        }
                    }
                    .padding(.bottom, 12)
                }
                .scrollIndicators(.hidden)
            }
            .padding(.horizontal, 16)
        }
        .toolbar(.visible, for: .navigationBar)
        .toolbarBackground(Theme.ground2, for: .navigationBar)
        .alert("Stop everything on the PC?", isPresented: $confirmStop) {
            Button("STOP ALL", role: .destructive) { Task { await session.stopEverything() } }
            Button("Cancel", role: .cancel) {}
        } message: { Text("JARVIS stops until RESUME is pressed on the PC.") }
        .task {
            do { history = try await session.client.history(conversation: conversationId, limit: 100) }
            catch { note = session.report(error) }
        }
    }
}
