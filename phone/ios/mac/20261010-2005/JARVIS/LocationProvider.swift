import Combine
import CoreLocation
import Foundation

/// The phone's position for "Send my location with questions" (round 5, R3 of docs/MAC-REQUESTS-20261007.md).
/// Asks iOS's "while using the app" permission the first time the switch goes on, keeps the last fix while the
/// switch is on, and hands out a fix no older than two minutes. Nothing is stored on the phone or sent anywhere
/// but inside a question to the Core, which keeps nothing unless the owner's words ask it to.
@MainActor
final class LocationProvider: NSObject, ObservableObject, CLLocationManagerDelegate {
    @Published private(set) var lastFix: CLLocation?
    @Published private(set) var denied = false
    private let manager = CLLocationManager()
    private var wanted = false

    override init() {
        super.init()
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyHundredMeters
        // Every new fix, moving or not: with a distance filter a phone sitting still gets no fix after the first,
        // and the two-minute limit then sends none (review of 2026-10-10, finding 3).
        manager.distanceFilter = kCLDistanceFilterNone
        manager.pausesLocationUpdatesAutomatically = false
    }

    /// The switch went on: ask once, then keep a fix while the app is in use.
    func start() {
        wanted = true
        switch manager.authorizationStatus {
        case .notDetermined: manager.requestWhenInUseAuthorization()
        case .authorizedWhenInUse, .authorizedAlways: manager.startUpdatingLocation()
        default: denied = true
        }
    }

    func stop() {
        wanted = false
        manager.stopUpdatingLocation()
        lastFix = nil
    }

    /// The fix to send with a question, or nil when there is none fresh enough.
    func current(maxAge: TimeInterval) -> QuestionLocation? {
        guard wanted, let fix = lastFix, Date().timeIntervalSince(fix.timestamp) <= maxAge else { return nil }
        // A fix iOS marks invalid (negative accuracy, coordinates out of range) is no fix: the Core refuses the
        // whole question when lat or lon is out of range ("Invalid location.").
        guard fix.horizontalAccuracy >= 0, CLLocationCoordinate2DIsValid(fix.coordinate) else { return nil }
        let accuracy = min(100_000, fix.horizontalAccuracy)
        return QuestionLocation(lat: fix.coordinate.latitude, lon: fix.coordinate.longitude, accuracyM: accuracy, label: nil)
    }

    nonisolated func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        let status = manager.authorizationStatus
        Task { @MainActor in
            switch status {
            case .authorizedWhenInUse, .authorizedAlways:
                self.denied = false
                if self.wanted { self.manager.startUpdatingLocation() }
            case .denied, .restricted:
                self.denied = true
            default:
                break
            }
        }
    }

    nonisolated func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let fix = locations.last else { return }
        Task { @MainActor in self.lastFix = fix }
    }

    nonisolated func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        // A failed fix is simply no fix: the next question goes without a location.
    }
}
