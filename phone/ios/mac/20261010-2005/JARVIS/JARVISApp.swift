import SwiftUI

// JARVIS for iPhone (round 3 of 2026-10-07, the command look): a client of the one Core on the owner's PC
// (docs/PHONE-PLAN.md, ROUND3-COMMAND-LOOK.md). Three screens, Ask, Chats and Overview, a pairing screen before
// them, a lock screen when the owner turns Face ID on, and the emergency stop on every screen.
@main
struct JARVISApp: App {
    @StateObject private var session = SessionModel()
    @Environment(\.scenePhase) private var scenePhase

    init() {
        let bar = UITabBarAppearance()
        bar.configureWithOpaqueBackground()
        bar.backgroundColor = UIColor(Theme.ground2)
        bar.stackedLayoutAppearance.normal.iconColor = UIColor(Theme.muted)
        bar.stackedLayoutAppearance.normal.titleTextAttributes = [.foregroundColor: UIColor(Theme.muted)]
        bar.stackedLayoutAppearance.selected.iconColor = UIColor(Theme.accent)
        bar.stackedLayoutAppearance.selected.titleTextAttributes = [.foregroundColor: UIColor(Theme.accent)]
        UITabBar.appearance().standardAppearance = bar
        UITabBar.appearance().scrollEdgeAppearance = bar
    }

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(session)
                .preferredColorScheme(.dark)
                .onOpenURL { url in session.handle(url: url) }   // jarvis://listen from the button, jarvis://stop
                .onChange(of: scenePhase) { _, phase in
                    switch phase {
                    case .active:
                        session.cameToFront()                 // the lock, when the owner has turned it on
                        Task { await session.connect() }      // hello again; pick up an answer the phone lost the link to, and what Siri added
                    case .background:
                        session.sceneInactive()               // first: anything it keeps for a return...
                        session.leftFront()                   // ...is dropped here; the lock's minute of grace counts from here
                    default:
                        session.sceneInactive()               // a recording in progress is dropped; a question runs on at the Core
                    }
                }
        }
    }
}

struct RootView: View {
    @EnvironmentObject private var session: SessionModel

    var body: some View {
        if !session.paired {
            PairingView()
        } else if session.locked {
            LockView()
        } else {
            MainTabs()
        }
    }
}

enum Screen: Int { case ask, chats, overview }

struct MainTabs: View {
    @EnvironmentObject private var session: SessionModel
    @State private var screen: Screen = .ask
    @State private var showApprovals = false
    @State private var showNotices = false

    var body: some View {
        TabView(selection: $screen) {
            AskView()
                .tabItem { Label("Ask", systemImage: "waveform.circle") }
                .tag(Screen.ask)
            ChatsView(showAsk: { screen = .ask })
                .tabItem { Label("Chats", systemImage: "bubble.left.and.bubble.right") }
                .tag(Screen.chats)
            OverviewView()
                .tabItem { Label("Overview", systemImage: "gauge.with.dots.needle.33percent") }
                .tag(Screen.overview)
        }
        .tint(Theme.accent)
        .task { await session.connect() }
        // One owner for the health polling (review of round 3, finding 1): Ask and Overview show the numbers, Chats
        // does not. The screens' own onAppear/onDisappear raced at a tab switch and cancelled the loop just started.
        .onChange(of: screen, initial: true) { _, shown in
            if shown == .chats { session.stopHealthPolling() } else { session.startHealthPolling() }
        }
        .onDisappear { session.stopHealthPolling() }   // the lock screen or the pairing screen took over
        .onChange(of: session.askRequested) { _, _ in screen = .ask }   // a button or link opened the app to ask
        // Round 6: a tap on the widget's approvals or notices count, at once or after the unlock (a request older
        // than two minutes, the unlock put off, is not acted on).
        .onChange(of: session.listRequest, initial: true) { _, request in
            guard let request else { return }
            session.takeListRequest()
            guard Date().timeIntervalSince(request.at) <= SessionModel.handsFreeMaxAge else { return }
            if request.kind == .approvals { showApprovals = true } else { showNotices = true }
        }
        // Round 6: a new approval or notice while the app is open, on every screen under the header (STOP ALL stays
        // uncovered above it, the microphone and the buttons below: review finding 9). 108 pt clears the deepest
        // header, an open conversation's (its navigation bar, then its header row with STOP ALL).
        .overlay(alignment: .top) {
            if let headsUp = session.headsUp {
                HeadsUpBanner(headsUp: headsUp) {
                    session.dismissHeadsUp()
                    if headsUp.kind == .approvals { showApprovals = true } else { showNotices = true }
                } close: {
                    session.dismissHeadsUp()
                }
                .padding(.horizontal, 16)
                .padding(.top, 108)
                .transition(.move(edge: .top).combined(with: .opacity))
            }
        }
        .animation(.easeInOut(duration: 0.25), value: session.headsUp)
        .sheet(isPresented: $showApprovals) { ApprovalsView() }
        .sheet(isPresented: $showNotices) { NoticesView() }
    }
}

/// Round 6: the heads-up itself. OPEN shows the list; the cross puts it away (it also goes by itself after 6 s).
struct HeadsUpBanner: View {
    let headsUp: HeadsUp
    let open: () -> Void
    let close: () -> Void

    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: headsUp.kind == .approvals ? "checkmark.seal" : "bell.badge")
                .font(.system(size: 16)).foregroundStyle(headsUp.kind == .approvals ? Theme.warn : Theme.accent)
            Text(headsUp.text).font(.system(size: 13, weight: .semibold)).foregroundStyle(Theme.text)
                .lineLimit(2)
            Spacer(minLength: 6)
            Button(action: open) {
                Text("OPEN").font(Theme.caption(10)).tracking(1.2).foregroundStyle(Theme.accent)
                    .padding(.horizontal, 12).frame(height: 30)
                    .overlay(RoundedRectangle(cornerRadius: 6).stroke(Theme.accent.opacity(0.6), lineWidth: 1))
                    .frame(minHeight: 44)
                    .contentShape(Rectangle())
            }
            .accessibilityLabel(headsUp.kind == .approvals ? "Open approvals" : "Open notices")
            Button(action: close) {
                Image(systemName: "xmark").font(.system(size: 12)).foregroundStyle(Theme.muted)
                    .frame(width: 44, height: 44)
                    .contentShape(Rectangle())
            }
            .accessibilityLabel("Put the notice away")
        }
        .padding(.leading, 14)
        .background(CutCornerRect(cut: 9).fill(Color(hex: 0x061522).opacity(0.96)))
        .overlay(CutCornerRect(cut: 9).stroke(Theme.accent.opacity(0.6), lineWidth: 1))
        .shadow(color: Theme.accent.opacity(0.3), radius: 8)
    }
}

/// STOP ALL for a sheet's toolbar (round 6, review finding 15: the emergency stop on every screen, the sheets
/// included), with the same question before it as everywhere else.
struct SheetStopButton: View {
    @EnvironmentObject private var session: SessionModel
    @State private var confirmStop = false

    var body: some View {
        StopButton(stopped: session.stopped) { confirmStop = true }
            .disabled(!session.paired)
            .alert("Stop everything on the PC?", isPresented: $confirmStop) {
                Button("STOP ALL", role: .destructive) { Task { await session.stopEverything() } }
                Button("Cancel", role: .cancel) {}
            } message: { Text("JARVIS stops until RESUME is pressed on the PC. The phone cannot resume.") }
    }
}

/// Before the screens, when the lock is on: Face ID or the passcode, asked as soon as this shows and again from the
/// UNLOCK button. The emergency stop is here too, without unlocking: stopping JARVIS needs no proof of who you are.
struct LockView: View {
    @EnvironmentObject private var session: SessionModel
    @State private var confirmStop = false

    var body: some View {
        ZStack {
            PageBackground()
            VStack(spacing: 16) {
                Spacer()
                JarvisMark().frame(width: 76, height: 76)
                Text("JARVIS").font(.system(size: 26, weight: .light)).foregroundStyle(Theme.text)
                Caption("Locked", color: Theme.accent, size: 9)
                Button {
                    Task { await session.unlock() }
                } label: {
                    HStack(spacing: 8) {
                        Image(systemName: "faceid").font(.system(size: 16))
                        Text("UNLOCK").font(Theme.caption(12)).tracking(1.5)
                    }
                    .frame(maxWidth: .infinity).frame(height: 46)
                    .background(Theme.accent)
                    .foregroundStyle(Theme.ground2)
                }
                .padding(.horizontal, 48).padding(.top, 8)
                Spacer()
                StopButton(stopped: session.stopped) { confirmStop = true }
                Text("The emergency stop works without unlocking.").font(.system(size: 10)).foregroundStyle(Theme.muted)
                    .padding(.bottom, 28)
            }
            .padding(.horizontal, 16)
        }
        .alert("Stop everything on the PC?", isPresented: $confirmStop) {
            Button("STOP ALL", role: .destructive) { Task { await session.stopEverything() } }
            Button("Cancel", role: .cancel) {}
        } message: { Text("JARVIS stops until RESUME is pressed on the PC.") }
        .onAppear { Task { await session.unlock() } }
    }
}
