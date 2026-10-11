import AppIntents
import Foundation

// Shared by the app and the JARVISControls extension (the folder is in both targets): the intent behind the
// "Ask JARVIS" button of the lock screen and Control Center. With `openAppWhenRun` the system opens the app and
// performs the intent there, so this is the app's own process: it leaves a time-stamped request that the session
// picks up at once (the notification) or as soon as it is in front (the stored time, good for two minutes), and
// listening starts hands-free. Nothing else is kept; the extension itself holds no key, address or logic.

struct OpenJarvisListeningIntent: AppIntent {
    static var title: LocalizedStringResource = "Open JARVIS listening"
    static var description = IntentDescription("Opens JARVIS and starts listening for a question.")
    static var openAppWhenRun: Bool = true
    static var isDiscoverable: Bool = false   // not a Siri phrase of its own: the app's "Ask JARVIS" shortcut serves Siri

    static let requestKey = "listen.requestAt"
    static let requestNotification = Notification.Name("com.teagueindustries.jarvis.listen-request")

    @MainActor
    func perform() async throws -> some IntentResult {
        UserDefaults.standard.set(Date(), forKey: Self.requestKey)
        NotificationCenter.default.post(name: Self.requestNotification, object: nil)
        return .result()
    }
}
