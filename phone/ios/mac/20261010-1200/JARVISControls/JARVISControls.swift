import AppIntents
import SwiftUI
import WidgetKit

// The JARVIS button for the lock screen and Control Center (round 4, 2026-10-07: the owner's wish for the side
// button, which Apple keeps for Siri). A control is the nearest thing iOS allows: one press opens the app listening,
// from the lock screen without unlocking first (the app's own Face ID lock still applies once it is open) or from
// Control Center anywhere. This extension holds no key, no address and no logic of its own: its button runs
// OpenJarvisListeningIntent (JARVISShared/, in both targets), which the system performs in the app after opening it.
// One Core, one JARVIS.

@main
struct JARVISControlsBundle: WidgetBundle {
    var body: some Widget {
        AskJarvisControl()
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
