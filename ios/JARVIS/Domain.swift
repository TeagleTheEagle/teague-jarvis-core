import Foundation

// Wire values match wearables/states.py. These are presentation events from Core,
// never a second reasoning state machine or a locally owned assistant identity.
enum JarvisState: String, CaseIterable, Codable, Sendable {
    case offline = "OFFLINE", idle = "IDLE", listening = "LISTENING"
    case thinking = "THINKING", looking = "LOOKING", speaking = "SPEAKING"
    case executing = "EXECUTING", error = "ERROR"
}

enum Capability: String, CaseIterable, Codable, Sendable {
    case display, microphone, speakers, camera, haptics, notifications
}

struct DeviceDescriptor: Equatable, Sendable {
    let id: String
    let capabilities: Set<Capability>
    let ready: Set<Capability>
    let simulated: Bool
}

struct MockPermissions: Equatable {
    var microphone = false
    var camera = false
    // A simulation must never enter the production registry as a real device.
    var descriptor: DeviceDescriptor {
        var ready: Set<Capability> = [.display, .speakers]
        if microphone { ready.insert(.microphone) }
        if camera { ready.insert(.camera) }
        return DeviceDescriptor(id: "ios-mock", capabilities: [.display, .speakers, .microphone, .camera],
                                ready: ready, simulated: true)
    }
}

enum MockScenario: String, CaseIterable, Identifiable {
    case conversation = "Conversation", voice = "Voice UI", vision = "Camera UI"
    case action = "Action UI", providerUnavailable = "Provider unavailable"
    case networkLoss = "Network loss", authorizationRevoked = "Device revoked"
    var id: String { rawValue }
}

enum CoreEvent: Equatable, Sendable {
    case state(JarvisState)
    case message(String)
}

enum ClientFailure: Error, LocalizedError, Equatable {
    case offline, unauthorized, permissionRequired(String), providerUnavailable
    case liveNotConfigured, invalidEndpoint, invalidResponse, busy
    var errorDescription: String? {
        switch self {
        case .offline: return "Core connection unavailable. Reconnect to continue."
        case .unauthorized: return "Device authorization revoked. Pairing is required."
        case .permissionRequired(let name): return "Simulated \(name) permission is denied. Enable it in the mock lab."
        case .providerUnavailable: return "The simulated AI service is unavailable. Your Core context would remain on the PC."
        case .liveNotConfigured: return "Live Core connection is not implemented in 0.1. No network request was sent."
        case .invalidEndpoint: return "Use an HTTPS Core address without credentials, query or fragment."
        case .invalidResponse: return "The Core returned an unsupported response."
        case .busy: return "An interaction is already in progress."
        }
    }
}

// The production implementation will authenticate with ONE running Core and use
// Core-issued conversation/project IDs. This is a client port, not a server API.
@MainActor
protocol CoreClient: AnyObject {
    var isMock: Bool { get }
    func connect(device: DeviceDescriptor) async throws
    func updateCapabilities(_ device: DeviceDescriptor) async throws
    func events(text: String, scenario: MockScenario) -> AsyncThrowingStream<CoreEvent, Error>
    func cancel()
    func disconnect()
}

@MainActor
final class UnconfiguredCoreClient: CoreClient {
    let isMock = false
    func connect(device: DeviceDescriptor) async throws { throw ClientFailure.liveNotConfigured }
    func updateCapabilities(_ device: DeviceDescriptor) async throws { throw ClientFailure.liveNotConfigured }
    func events(text: String, scenario: MockScenario) -> AsyncThrowingStream<CoreEvent, Error> {
        AsyncThrowingStream { $0.finish(throwing: ClientFailure.liveNotConfigured) }
    }
    func cancel() {}
    func disconnect() {}
}
