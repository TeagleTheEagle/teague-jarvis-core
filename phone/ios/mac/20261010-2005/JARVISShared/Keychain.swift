import Foundation
import Security

/// The device's key lives in the iPhone Keychain and nowhere else (docs/PHONE-PLAN.md section 6).
/// This device only, never backed up to another device. Since round 6 (2026-10-10, the owner's "I OK the Apple
/// account change") it is kept in the App Group's keychain group, so that the widget and Share to JARVIS, the app's
/// own extensions, can use it too; iOS counts an app's App Groups among its keychain access groups.
enum Keychain {
    private static let service = "com.teagueindustries.jarvis.device"
    private static let account = "credential"
    /// The keychain group the app shares with its extensions: the App Group.
    static let sharedGroup = SharedStore.appGroup

    /// The key: from the shared group, or from the app's own group where it was kept before round 6.
    static func read() -> String? { read(in: sharedGroup) ?? read(in: nil) }

    /// What the widget needs to tell apart: a key, no key at all (this phone is not paired), or a key that cannot be
    /// read now (the phone restarted and has not been unlocked since).
    enum Lookup { case found(String), notFound, unreadable }

    static func lookup() -> Lookup {
        var query = query(nil)
        query[kSecReturnData as String] = true
        query[kSecMatchLimit as String] = kSecMatchLimitOne
        var item: CFTypeRef?
        switch SecItemCopyMatching(query as CFDictionary, &item) {
        case errSecSuccess:
            guard let data = item as? Data, let text = String(data: data, encoding: .utf8), !text.isEmpty else { return .notFound }
            return .found(text)
        case errSecItemNotFound:
            return .notFound
        default:
            return .unreadable   // errSecInteractionNotAllowed before the first unlock, or another fault
        }
    }

    private static func query(_ group: String?) -> [String: Any] {
        var query: [String: Any] = [kSecClass as String: kSecClassGenericPassword,
                                    kSecAttrService as String: service,
                                    kSecAttrAccount as String: account]
        if let group { query[kSecAttrAccessGroup as String] = group }
        return query
    }

    private static func read(in group: String?) -> String? {
        var query = query(group)
        query[kSecReturnData as String] = true
        query[kSecMatchLimit as String] = kSecMatchLimitOne
        var item: CFTypeRef?
        guard SecItemCopyMatching(query as CFDictionary, &item) == errSecSuccess,
              let data = item as? Data, let text = String(data: data, encoding: .utf8), !text.isEmpty else { return nil }
        return text
    }

    /// Kept in the shared group; only when that group is not there (a build without the App Group) in the app's own.
    @discardableResult
    static func write(_ credential: String) -> Bool {
        if write(credential, in: sharedGroup) {
            // An older copy, from before a new pairing, never lingers; but only once the new key reads back the same
            // from the shared group, so the key just written is never the one removed.
            if read(in: sharedGroup) == credential { removeOutsideSharedGroup() }
            return true
        }
        return write(credential, in: nil)
    }

    private static func write(_ credential: String, in group: String?) -> Bool {
        let data = Data(credential.utf8)
        let query = query(group)
        let attributes: [String: Any] = [kSecValueData as String: data,
                                         kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly]
        let updated = SecItemUpdate(query as CFDictionary, attributes as CFDictionary)
        if updated == errSecSuccess { return true }
        if updated != errSecItemNotFound { SecItemDelete(query as CFDictionary) }   // an item that cannot be updated is replaced
        var insert = query
        for (k, v) in attributes { insert[k] = v }
        return SecItemAdd(insert as CFDictionary, nil) == errSecSuccess
    }

    /// Once, at the app's start: a key kept before round 6 is copied into the shared group; the old copy goes only
    /// when the new one reads back the same, so the pairing is never lost on the way.
    static func shareWithExtensions() {
        guard read(in: sharedGroup) == nil, let old = read(in: nil) else { return }
        guard write(old, in: sharedGroup), read(in: sharedGroup) == old else { return }
        removeOutsideSharedGroup()
    }

    /// Every copy in a group other than the shared one (the app's own group, before round 6).
    private static func removeOutsideSharedGroup() {
        var query = query(nil)
        query[kSecReturnAttributes as String] = true
        query[kSecMatchLimit as String] = kSecMatchLimitAll
        var items: CFTypeRef?
        guard SecItemCopyMatching(query as CFDictionary, &items) == errSecSuccess,
              let found = items as? [[String: Any]] else { return }
        for attributes in found {
            guard let group = attributes[kSecAttrAccessGroup as String] as? String, group != sharedGroup else { continue }
            SecItemDelete(Self.query(group) as CFDictionary)
        }
    }

    /// Every copy, in every group (a forgotten pairing, a refused key).
    static func delete() {
        SecItemDelete(query(nil) as CFDictionary)
    }
}

/// What the app keeps outside the Keychain: the Core's address, the pairing's name, the conversation in progress
/// and the choices of the settings sheet. The address, the pairing's id and name and the lock choice are also kept
/// in the App Group (round 6), where the widget and Share to JARVIS read them; they are read from there first.
enum AppSettings {
    private static let defaults = UserDefaults.standard
    private static let shared = SharedStore.defaults

    private static func string(_ key: String) -> String? { shared?.string(forKey: key) ?? defaults.string(forKey: key) }
    private static func setBoth(_ value: Any?, _ key: String) {
        defaults.set(value, forKey: key)
        shared?.set(value, forKey: key)
    }

    static var address: CoreAddress? {
        get {
            guard let host = string("core.host"), !host.isEmpty else { return nil }
            let port = (shared?.object(forKey: "core.port") as? Int) ?? defaults.integer(forKey: "core.port")
            return CoreAddress(host: host, port: port == 0 ? CoreAddress.defaultPort : port)
        }
        set {
            setBoth(newValue?.host, "core.host")
            setBoth(newValue?.port ?? 0, "core.port")
        }
    }

    static var deviceId: String? {
        get { string("device.id") }
        set { setBoth(newValue, "device.id") }
    }

    static var deviceName: String? {
        get { string("device.name") }
        set { setBoth(newValue, "device.name") }
    }

    /// Once, at the app's start: what the app kept before round 6 is copied into the App Group.
    static func shareWithExtensions() {
        // A question an older build left for the app to send ("Hey Siri, ask JARVIS" opened the app until round 6;
        // Siri answers in place now): never sent any more, so not kept.
        defaults.removeObject(forKey: "siri.question")
        defaults.removeObject(forKey: "siri.questionAt")
        guard let shared else { return }
        for key in ["core.host", "core.port", "device.id", "device.name", "lock.enabled"]
        where shared.object(forKey: key) == nil {
            if let value = defaults.object(forKey: key) { shared.set(value, forKey: key) }
        }
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
        get { (shared?.object(forKey: "lock.enabled") as? Bool) ?? defaults.bool(forKey: "lock.enabled") }
        set { setBoth(newValue, "lock.enabled") }
    }

    /// "Send my location with questions" (round 5, R3): off until the owner turns it on in the settings sheet.
    static var sendLocation: Bool {
        get { defaults.bool(forKey: "location.send") }
        set { defaults.set(newValue, forKey: "location.send") }
    }

    static func forgetPairing() {
        Keychain.delete()
        deviceId = nil
        deviceName = nil
        conversation = nil
    }
}
