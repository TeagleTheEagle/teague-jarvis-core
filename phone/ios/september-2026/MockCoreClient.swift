import Foundation

// Explicit fixture service: no prompts, inference, files, credentials, memory or API calls.
@MainActor
final class MockCoreClient: CoreClient {
    let isMock = true
    private(set) var registeredDevice: DeviceDescriptor?
    private var pending: AsyncThrowingStream<CoreEvent, Error>.Continuation?
    private var producer: Task<Void, Never>?
    private var generation = 0
    private let delay: UInt64

    init(stepNanoseconds: UInt64 = 650_000_000) { delay = stepNanoseconds }

    func connect(device: DeviceDescriptor) async throws {
        guard device.simulated, device.ready.isSubset(of: device.capabilities) else {
            throw ClientFailure.invalidResponse
        }
        cancel()
        registeredDevice = device
    }

    func updateCapabilities(_ device: DeviceDescriptor) async throws {
        guard let registeredDevice else { throw ClientFailure.offline }
        guard device.id == registeredDevice.id, device.simulated,
              device.ready.isSubset(of: device.capabilities) else { throw ClientFailure.invalidResponse }
        cancel()
        self.registeredDevice = device
    }

    func events(text: String, scenario: MockScenario) -> AsyncThrowingStream<CoreEvent, Error> {
        guard producer == nil else { return AsyncThrowingStream { $0.finish(throwing: ClientFailure.busy) } }
        let stream = AsyncThrowingStream<CoreEvent, Error>.makeStream()
        guard let device = registeredDevice else {
            stream.continuation.finish(throwing: ClientFailure.offline)
            return stream.stream
        }
        if scenario == .voice && !device.ready.contains(.microphone) {
            stream.continuation.finish(throwing: ClientFailure.permissionRequired("microphone"))
            return stream.stream
        }
        if scenario == .vision && !device.ready.contains(.camera) {
            stream.continuation.finish(throwing: ClientFailure.permissionRequired("camera"))
            return stream.stream
        }
        generation += 1
        let ticket = generation
        let delay = delay
        pending = stream.continuation
        producer = Task { [weak self] in
            do {
                var states: [JarvisState] = [.listening, .thinking]
                if scenario == .vision { states += [.looking, .thinking] }
                if scenario == .action { states += [.executing, .thinking] }
                for state in states {
                    try Task.checkCancellation()
                    stream.continuation.yield(.state(state))
                    try await Task.sleep(nanoseconds: delay)
                }
                switch scenario {
                case .providerUnavailable: throw ClientFailure.providerUnavailable
                case .networkLoss: throw ClientFailure.offline
                case .authorizationRevoked: throw ClientFailure.unauthorized
                default: break
                }
                stream.continuation.yield(.message(Self.fixture(for: scenario)))
                stream.continuation.yield(.state(.speaking))
                try await Task.sleep(nanoseconds: delay)
                try Task.checkCancellation()
                stream.continuation.yield(.state(.idle))
                stream.continuation.finish()
            } catch {
                stream.continuation.finish(throwing: error)
            }
            if let self, self.generation == ticket {
                self.producer = nil
                self.pending = nil
            }
        }
        stream.continuation.onTermination = { [weak self] _ in
            Task { @MainActor in
                if let self, self.generation == ticket { self.cancel() }
            }
        }
        return stream.stream
    }

    private static func fixture(for scenario: MockScenario) -> String {
        switch scenario {
        case .vision: return "Camera flow preview complete. No image was captured or analysed."
        case .voice: return "Voice interface preview complete. No microphone or speech service was used."
        case .action: return "Action flow preview complete. Nothing was executed on your devices."
        default: return "Connection preview complete. In live mode, this response will come from your existing JARVIS Core."
        }
    }

    func cancel() {
        generation += 1
        producer?.cancel()
        producer = nil
        pending?.finish(throwing: CancellationError())
        pending = nil
    }

    func disconnect() { cancel(); registeredDevice = nil }
}
