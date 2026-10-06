import Foundation
import Security

/// The device's key lives in the iPhone Keychain and nowhere else (docs/PHONE-PLAN.md section 6).
/// This device only, never backed up to another device.
enum Keychain {
    private static let service = "com.teagueindustries.jarvis.device"
    private static let account = "credential"

    static func read() -> String? {
        let query: [String: Any] = [kSecClass as String: kSecClassGenericPassword,
                                    kSecAttrService as String: service,
                                    kSecAttrAccount as String: account,
                                    kSecReturnData as String: true,
                                    kSecMatchLimit as String: kSecMatchLimitOne]
        var item: CFTypeRef?
        guard SecItemCopyMatching(query as CFDictionary, &item) == errSecSuccess,
              let data = item as? Data, let text = String(data: data, encoding: .utf8), !text.isEmpty else { return nil }
        return text
    }

    @discardableResult
    static func write(_ credential: String) -> Bool {
        let data = Data(credential.utf8)
        let query: [String: Any] = [kSecClass as String: kSecClassGenericPassword,
                                    kSecAttrService as String: service,
                                    kSecAttrAccount as String: account]
        let attributes: [String: Any] = [kSecValueData as String: data,
                                         kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly]
        let updated = SecItemUpdate(query as CFDictionary, attributes as CFDictionary)
        if updated == errSecSuccess { return true }
        if updated != errSecItemNotFound { SecItemDelete(query as CFDictionary) }   // an item that cannot be updated is replaced
        var insert = query
        for (k, v) in attributes { insert[k] = v }
        return SecItemAdd(insert as CFDictionary, nil) == errSecSuccess
    }

    static func delete() {
        let query: [String: Any] = [kSecClass as String: kSecClassGenericPassword,
                                    kSecAttrService as String: service,
                                    kSecAttrAccount as String: account]
        SecItemDelete(query as CFDictionary)
    }
}

/// What the app keeps outside the Keychain: the Core's address, the pairing's name, the conversation in progress,
/// the two choices of the settings sheet, and a question Siri took that the app has not sent yet.
enum AppSettings {
    private static let defaults = UserDefaults.standard

    static var address: CoreAddress? {
        get {
            guard let host = defaults.string(forKey: "core.host"), !host.isEmpty else { return nil }
            let port = defaults.integer(forKey: "core.port")
            return CoreAddress(host: host, port: port == 0 ? CoreAddress.defaultPort : port)
        }
        set {
            defaults.set(newValue?.host, forKey: "core.host")
            defaults.set(newValue?.port ?? 0, forKey: "core.port")
        }
    }

    static var deviceId: String? {
        get { defaults.string(forKey: "device.id") }
        set { defaults.set(newValue, forKey: "device.id") }
    }

    static var deviceName: String? {
        get { defaults.string(forKey: "device.name") }
        set { defaults.set(newValue, forKey: "device.name") }
    }

    /// The conversation the Ask screen continues when the app comes back.
    static var conversation: String? {
        get { defaults.string(forKey: "conversation.current") }
        set { defaults.set(newValue, forKey: "conversation.current") }
    }

    /// Whether replies are spoken (on until the owner turns it off in the settings sheet or with the Voice button).
    static var speakReplies: Bool {
        get { (defaults.object(forKey: "voice.speakReplies") as? Bool) ?? true }
        set { defaults.set(newValue, forKey: "voice.speakReplies") }
    }

    /// Face ID (or the passcode) before the screens show. Off until the owner turns it on in the settings sheet:
    /// the Xcode project needs the Info entry "Privacy - Face ID Usage Description" first (phone/ios/README-round2.md),
    /// and without that entry iOS ends the app at the first Face ID prompt.
    static var lockEnabled: Bool {
        get { defaults.bool(forKey: "lock.enabled") }
        set { defaults.set(newValue, forKey: "lock.enabled") }
    }

    /// "Hey Siri, ask JARVIS": the question Siri took, kept until the app (in front and unlocked) sends it, and when
    /// Siri took it (a question older than two minutes is dropped, not sent into a later conversation unasked).
    static var siriQuestion: String? {
        get { defaults.string(forKey: "siri.question") }
        set { defaults.set(newValue, forKey: "siri.question") }
    }

    static var siriQuestionAt: Date? {
        get { defaults.object(forKey: "siri.questionAt") as? Date }
        set { defaults.set(newValue, forKey: "siri.questionAt") }
    }

    static func forgetPairing() {
        Keychain.delete()
        deviceId = nil
        deviceName = nil
        conversation = nil
        siriQuestion = nil
        siriQuestionAt = nil
    }
}
