import Foundation
import Combine

struct DisplayMessage: Identifiable {
    let id = UUID()
    let isUser: Bool
    let text: String
}

@MainActor
final class SessionModel: ObservableObject {
    @Published private(set) var state: JarvisState = .offline
    @Published private(set) var connected = false
    @Published private(set) var busy = false
    @Published private(set) var messages: [DisplayMessage] = []
    @Published private(set) var notice: String?
    @Published private(set) var permissions = MockPermissions()
    @Published private(set) var stateHistory: [JarvisState] = [.offline]
    @Published var scenario: MockScenario = .conversation
    @Published var draft = ""
    let client: any CoreClient
    private var work: Task<Void, Never>?
    private var generation = 0

    init(client: any CoreClient) { self.client = client }
    var isMock: Bool { client.isMock }

    func connect() async {
        generation += 1
        let ticket = generation
        work?.cancel(); client.cancel(); busy = false
        do {
            try await client.connect(device: permissions.descriptor)
            guard generation == ticket else { return }
            connected = true; notice = nil; setState(.idle)
        } catch {
            guard generation == ticket else { return }
            fail(error)
        }
    }

    func disconnect() {
        generation += 1
        work?.cancel(); work = nil
        client.disconnect(); busy = false; connected = false
        setState(.offline)
    }

    func setPermission(_ capability: Capability, allowed: Bool) async {
        interrupt()
        if capability == .microphone { permissions.microphone = allowed }
        if capability == .camera { permissions.camera = allowed }
        if connected {
            do { try await client.updateCapabilities(permissions.descriptor) }
            catch { fail(error) }
        }
    }

    func send() {
        let text = draft.trimmingCharacters(in: .whitespacesAndNewlines)
        guard connected, !busy, !text.isEmpty, text.count <= 2000 else { return }
        generation += 1
        let ticket = generation
        busy = true; notice = nil; draft = ""
        messages.append(DisplayMessage(isUser: true, text: text))
        messages = Array(messages.suffix(60)) // Ephemeral presentation buffer, never canonical history.
        let events = client.events(text: text, scenario: scenario)
        work = Task { [weak self] in
            do {
                for try await event in events {
                    guard let self, self.generation == ticket, !Task.isCancelled else { return }
                    switch event {
                    case .state(let state): self.setState(state)
                    case .message(let text):
                        self.messages.append(DisplayMessage(isUser: false, text: text))
                        self.messages = Array(self.messages.suffix(60))
                    }
                }
                guard let self, self.generation == ticket else { return }
                self.busy = false
            } catch {
                guard let self, self.generation == ticket else { return }
                self.busy = false
                if !(error is CancellationError) { self.fail(error) }
            }
        }
    }

    func interrupt() {
        generation += 1; work?.cancel(); work = nil
        client.cancel(); busy = false
        if connected { setState(.idle) }
    }

    func clearPreview() { interrupt(); messages = []; notice = nil }

    private func setState(_ next: JarvisState) {
        state = next; stateHistory.append(next)
        stateHistory = Array(stateHistory.suffix(40))
    }

    private func fail(_ error: Error) {
        notice = (error as? ClientFailure)?.errorDescription ?? "Connection failed. Try reconnecting."
        if let failure = error as? ClientFailure,
           [.offline, .unauthorized, .liveNotConfigured].contains(failure) {
            client.disconnect(); connected = false; setState(.offline)
        } else { setState(.error) }
    }
}
