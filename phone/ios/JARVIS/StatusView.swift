import SwiftUI

/// Screen 3 of the canvas: this phone's pairing and link, the PC's health as the dashboard has it, and the
/// overview of tasks, projects and reminders. Real data only; what the PC does not measure is not shown.
struct StatusView: View {
    @EnvironmentObject private var session: SessionModel
    @State private var showSettings = false
    @State private var confirmStop = false

    var body: some View {
        ZStack {
            PageBackground()
            VStack(spacing: 8) {
                ScreenHeader(subtitle: "Status & profile") {
                    HStack(spacing: 10) {
                        HStack(spacing: 6) {
                            StatusDot(color: session.reached ? Theme.good : Theme.muted)
                            Caption(session.reached ? "Online" : "Not reached", color: Theme.text, size: 9)
                        }
                        StopButton(stopped: session.stopped) { confirmStop = true }
                        IconButton(system: "gearshape", label: "Phone settings") { showSettings = true }
                    }
                }
                ScrollView {
                    VStack(spacing: 8) {
                        phoneCard
                        healthCard
                        overviewCard
                        if let note = session.healthNote {
                            Text(note).font(.system(size: 11)).foregroundStyle(Theme.warn).multilineTextAlignment(.center)
                        }
                        if let metrics = session.metrics {
                            Text("Read by the JARVIS Core at \(Date(timeIntervalSince1970: metrics.sampledAt).formatted(date: .omitted, time: .standard)). Graphics, temperature and network traffic are not measured.")
                                .font(.system(size: 10)).foregroundStyle(Theme.muted.opacity(0.8)).multilineTextAlignment(.center).padding(.top, 4)
                        }
                    }
                    .padding(.bottom, 12)
                }
                .scrollIndicators(.hidden)
                .refreshable { await session.refreshHealth(overviewToo: true) }
            }
            .padding(.horizontal, 16)
        }
        .sheet(isPresented: $showSettings) { SettingsSheet() }
        .alert("Stop everything on the PC?", isPresented: $confirmStop) {
            Button("STOP ALL", role: .destructive) { Task { await session.stopEverything() } }
            Button("Cancel", role: .cancel) {}
        } message: { Text("JARVIS stops until RESUME is pressed on the PC.") }
        .onAppear { session.startHealthPolling() }
        .onDisappear { session.stopHealthPolling() }
    }

    // MARK: this phone

    private var phoneCard: some View {
        Panel {
            VStack(alignment: .leading, spacing: 10) {
                HStack {
                    VStack(alignment: .leading, spacing: 3) {
                        Text("THIS PHONE").font(.system(size: 11, weight: .semibold)).foregroundStyle(Theme.text)
                        HStack(spacing: 6) {
                            StatusDot(color: session.reached ? Theme.good : Theme.muted)
                            Caption(session.reached ? "Reached" : "Not reached", color: session.reached ? Theme.good : Theme.muted, size: 9)
                        }
                    }
                    Spacer()
                    Text("DEV \(String(AppSettings.deviceId?.prefix(4) ?? ""))…\(String(AppSettings.deviceId?.suffix(4) ?? ""))")
                        .font(Theme.mono(9)).foregroundStyle(Theme.muted.opacity(0.7))
                }
                HStack(spacing: 8) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("JARVIS CORE").font(.system(size: 14, weight: .semibold)).foregroundStyle(Theme.text)
                        Text(session.deviceName ?? "This phone").font(.system(size: 11)).foregroundStyle(Theme.muted)
                    }
                    Spacer()
                    HStack(spacing: 5) { Circle().fill(Theme.good).frame(width: 4, height: 4); Text("PAIRED") }
                        .font(Theme.caption(9)).foregroundStyle(Theme.good)
                        .padding(.horizontal, 7).frame(height: 20)
                        .overlay(RoundedRectangle(cornerRadius: 3).stroke(Theme.good.opacity(0.5), lineWidth: 1))
                }
                Rectangle().fill(LinearGradient(colors: [Theme.accent.opacity(0.35), .clear], startPoint: .leading, endPoint: .trailing)).frame(height: 1)
                row("Connection", session.reached ? (session.roundTripMs.map { "Reached · \($0) ms round trip" } ?? "Reached") : "Not reached", good: session.reached)
                row("Address", session.address.map { "\($0.host):\($0.port)" } ?? "—", good: nil)
                row("Core version", session.metrics?.coreVersion ?? "—", good: nil)
                row("Emergency stop", session.stopped ? "STOPPED · press RESUME on the PC" : "Not stopped", good: !session.stopped)
                row("May save", (session.info?.writes ?? false) ? "Memories and tasks (ticked on the PC)" : "Questions and reading only", good: nil)
            }
        }
    }

    private func row(_ label: String, _ value: String, good: Bool?) -> some View {
        HStack(alignment: .firstTextBaseline, spacing: 8) {
            Caption(label, size: 8).frame(width: 96, alignment: .leading)
            Text(value).font(.system(size: 11)).foregroundStyle(Theme.text)
            if let good { Image(systemName: good ? "checkmark" : "exclamationmark.triangle").font(.system(size: 9)).foregroundStyle(good ? Theme.good : Theme.bad) }
            Spacer()
        }
    }

    // MARK: the PC's health

    private var healthCard: some View {
        Panel(marked: false) {
            VStack(alignment: .leading, spacing: 10) {
                HStack {
                    Text("SYSTEM HEALTH").font(.system(size: 11, weight: .semibold)).foregroundStyle(Theme.text)
                    Spacer()
                    HStack(spacing: 6) {
                        Caption(session.metrics == nil ? "Not read yet" : (session.metrics!.aiReady ? "AI ready" : "No AI key on the PC"), size: 8)
                        StatusDot(color: session.metrics?.aiReady ?? false ? Theme.good : Theme.warn)
                    }
                }
                HStack(spacing: 10) {
                    HealthGauge(label: "CPU", value: session.metrics?.cpuPercent, unit: "%")
                    HealthGauge(label: "Memory", value: session.metrics?.memory?.usedPercent, unit: "%")
                    HealthGauge(label: "Storage", value: session.metrics?.disk?.usedPercent, unit: "%")
                    HealthGauge(label: "Link", value: session.roundTripMs.map(Double.init), unit: "ms", scale: 1000)
                }
                .frame(maxWidth: .infinity)
                if let metrics = session.metrics {
                    HStack(spacing: 14) {
                        Caption("Core up \(Self.uptime(metrics.coreUptimeSeconds))", size: 8)
                        if let ms = metrics.lastResponseMs { Caption("Last reply \(String(format: "%.1f", ms / 1000)) s", size: 8) }
                    }
                }
            }
        }
    }

    static func uptime(_ seconds: Int?) -> String {
        guard let seconds else { return "—" }
        if seconds < 3600 { return "\(seconds / 60) min" }
        if seconds < 86400 { return "\(seconds / 3600) h \((seconds % 3600) / 60) min" }
        return "\(seconds / 86400) d \((seconds % 86400) / 3600) h"
    }

    // MARK: overview

    private var overviewCard: some View {
        Panel(marked: false) {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("OVERVIEW").font(.system(size: 11, weight: .semibold)).foregroundStyle(Theme.text)
                    Spacer()
                    if let overview = session.overview { Caption("\(overview.tasksOpen) open tasks", color: Theme.accent, size: 8) }
                }
                if let overview = session.overview {
                    if overview.projects.isEmpty {
                        Text("No projects on the PC.").font(.system(size: 11)).foregroundStyle(Theme.muted)
                    }
                    ForEach(overview.projects) { project in
                        HStack(spacing: 9) {
                            Image(systemName: "folder").font(.system(size: 12)).foregroundStyle(Theme.accent)
                            Text(project.name).font(.system(size: 11.5, weight: .semibold)).foregroundStyle(Theme.text).lineLimit(1)
                            Spacer()
                            Text(project.openTasks == 0 ? "no tasks" : "\(project.openTasks) open").font(.system(size: 9)).foregroundStyle(Theme.muted)
                        }
                    }
                    Rectangle().fill(Theme.accent.opacity(0.1)).frame(height: 1)
                    HStack {
                        Caption("Upcoming", size: 8)
                        Spacer()
                        Caption(overview.reminders.isEmpty ? "Nothing in the next 24 hours" : "\(overview.reminders.count) in 24 h", color: Theme.accent, size: 8)
                    }
                    ForEach(Array(overview.reminders.enumerated()), id: \.offset) { _, reminder in
                        HStack(spacing: 10) {
                            Text(Date(timeIntervalSince1970: reminder.due).formatted(date: .omitted, time: .shortened))
                                .font(.system(size: 11)).foregroundStyle(Theme.accent).frame(width: 64, alignment: .leading)
                            Text(reminder.title).font(.system(size: 11)).foregroundStyle(reminder.fired ? Theme.muted : Theme.text).lineLimit(1)
                            Spacer()
                            if reminder.fired { Caption("Done", size: 7.5) }
                        }
                    }
                } else {
                    Text("Not read yet.").font(.system(size: 11)).foregroundStyle(Theme.muted)
                }
            }
        }
    }
}

/// A ring with the value in it, as the canvas draws CPU, memory, storage and link. (Not SwiftUI's own Gauge.)
struct HealthGauge: View {
    let label: String
    let value: Double?
    let unit: String
    var scale: Double = 100

    private var share: Double { min(1, max(0, (value ?? 0) / scale)) }
    private var color: Color {
        guard value != nil else { return Theme.muted }
        if unit == "%" && share > 0.9 { return Theme.bad }
        if unit == "%" && share > 0.75 { return Theme.warn }
        return Theme.accent
    }

    var body: some View {
        VStack(spacing: 5) {
            ZStack {
                Circle().stroke(Theme.accent.opacity(0.15), lineWidth: 4)
                Circle().trim(from: 0, to: share).stroke(color, style: StrokeStyle(lineWidth: 4, lineCap: .round))
                    .rotationEffect(.degrees(-90))
                VStack(spacing: 1) {
                    Caption(label, size: 7)
                    HStack(alignment: .firstTextBaseline, spacing: 1) {
                        Text(value.map { "\(Int($0.rounded()))" } ?? "—").font(.system(size: 15, weight: .light)).foregroundStyle(Theme.text)
                        Text(unit).font(.system(size: 8)).foregroundStyle(Theme.muted)
                    }
                }
            }
            .frame(width: 70, height: 70)
        }
        .frame(maxWidth: .infinity)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("\(label): \(value.map { "\(Int($0.rounded())) \(unit)" } ?? "not read")")
    }
}
