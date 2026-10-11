import AppIntents
import SwiftUI
import WidgetKit

// The JARVIS button for the lock screen and Control Center (round 4, 2026-10-07: the owner's wish for the side
// button, which Apple keeps for Siri), and since round 6 the Home Screen widget (JarvisStatusWidget.swift). The
// button is the nearest thing iOS allows: one press opens the app listening, from the lock screen without unlocking
// first (the app's own Face ID lock still applies once it is open) or from Control Center anywhere. Its intent,
// OpenJarvisListeningIntent (JARVISShared/, in both targets), is performed by the system in the app after opening it.
// The widget reads the Core's status with this phone's key from the shared Keychain group; it changes nothing.
// One Core, one JARVIS.

@main
struct JARVISControlsBundle: WidgetBundle {
    var body: some Widget {
        AskJarvisControl()
        JarvisStatusWidget()
    }
}

/// "Ask JARVIS": the button. The owner adds it in Control Center's or the lock screen's customise view, where it
/// is listed under the app's name.
struct AskJarvisControl: ControlWidget {
    static let kind = "com.teagueindustries.jarvis.controls.ask"

    var body: some ControlWidgetConfiguration {
        StaticControlConfiguration(kind: Self.kind) {
            ControlWidgetButton(action: OpenJarvisListeningIntent()) {
                Label("Ask JARVIS", systemImage: "waveform.circle")
            }
        }
        .displayName("Ask JARVIS")
        .description("Opens JARVIS listening. Speak, and the question goes when you pause.")
    }
}
