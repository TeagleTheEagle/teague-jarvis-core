import Foundation

// Shared by the app and its extensions (the widget, Share to JARVIS): what the app says about itself, and the one
// App Group they share (round 6, 2026-10-10, on the owner's "I OK the Apple account change").

/// What the app says about itself: the version from the bundle, never a typed number.
enum AppInfo {
    static var version: String {
        Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "—"
    }
}

/// The App Group of the app and its two extensions. It holds the Core's address and this pairing's id, name and
/// lock choice, mirrored by the app (AppSettings); the device key stays in the Keychain, in the same group
/// (Keychain.sharedGroup). Nothing else is shared: the widget asks the Core itself each time it is drawn.
enum SharedStore {
    static let appGroup = "group.com.teagueindustries.jarvis"
    static let defaults = UserDefaults(suiteName: appGroup)
}

/// The Home Screen widget's kind (JARVISControls), known to the app so that it can ask iPhone to draw the widget
/// again when the stop or a count changes while the app is open.
enum WidgetKinds {
    static let status = "com.teagueindustries.jarvis.widget.status"
}
