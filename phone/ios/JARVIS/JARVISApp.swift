import SwiftUI

// JARVIS for iPhone, version 1: a client of the one Core on the owner's PC (docs/PHONE-PLAN.md). Three screens,
// Ask, Chats and Status, a pairing screen before them, and the emergency stop on every screen.
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
                    case .active: Task { await session.connect() }   // hello again, and pick up an answer the phone lost the link to
                    default: session.sceneInactive()                 // a recording in progress is dropped; a question runs on at the Core
                    }
                }
        }
    }
}

struct RootView: View {
    @EnvironmentObject private var session: SessionModel

    var body: some View {
        if session.paired {
            MainTabs()
        } else {
            PairingView()
        }
    }
}

enum Screen: Int { case ask, chats, status }

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
            StatusView()
                .tabItem { Label("Status", systemImage: "gauge.with.dots.needle.33percent") }
                .tag(Screen.status)
        }
        .tint(Theme.accent)
        .task { await session.connect() }
    }
}
