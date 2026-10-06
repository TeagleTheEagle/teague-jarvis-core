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
                .onChange(of: scenePhase) { _, phase in
                    switch phase {
                    case .active:
                        session.cameToFront()                 // the lock, when the owner has turned it on
                        Task { await session.connect() }      // hello again; pick up an answer the phone lost the link to, or a Siri question
                    case .background:
                        session.leftFront()                   // the lock's minute of grace counts from here
                        session.sceneInactive()
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
