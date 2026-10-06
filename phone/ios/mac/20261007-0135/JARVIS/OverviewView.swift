import SwiftUI

/// Screen 3, the command look (ROUND3-COMMAND-LOOK.md): the brand strip and the clock, the core, the six systems
/// and their ring, live diagnostics with sparklines, voice input with a live waveform, the projects, the day's
/// reminders, this phone. Real data only: every value comes from the Core's hello/status, metrics and overview
/// replies, or is this phone's own (its clock, its microphone level, its round trip). What the PC does not
/// measure is not shown.
struct OverviewView: View {
    @EnvironmentObject private var session: SessionModel
    @State private var showSettings = false
    @State private var confirmStop = false

    var body: some View {
        ZStack {
            PageBackground()
            VStack(spacing: 8) {
                ScreenHeader(subtitle: "Command overview") {
                    HStack(spacing: 8) {
                        HeaderState(state: session.state)
                        StopButton(stopped: session.stopped) { confirmStop = true }
                        IconButton(system: "gearshape", label: "Phone settings") { showSettings = true }
                    }
                }
                ScrollView {
                    VStack(spacing: 10) {
                        HudStrip()
                        corePanel
                        systemStatusPanel
                        diagnosticsPanel
                        projectsPanel
                        upcomingPanel
                        phonePanel
                        if let note = session.healthNote {
                            Text(note).font(.system(size: 11)).foregroundStyle(Theme.warn).multilineTextAlignment(.center)
                        }
                        footer
                    }
                    .padding(.bottom, 12)
                }
                .scrollIndicators(.hidden)
                .refreshable { await session.refreshHealth(overviewToo: true) }
                // Outside the scroll view, as on Ask: a hold on the microphone must never be handed to a scroll,
                // which would leave the microphone open (review of round 3, finding 2).
                voicePanel
            }
            .padding(.horizontal, 16)
            .padding(.bottom, 8)
        }
        .sheet(isPresented: $showSettings) { SettingsSheet() }
        .alert("Stop everything on the PC?", isPresented: $confirmStop) {
            Button("STOP ALL", role: .destructive) { Task { await session.stopEverything() } }
            Button("Cancel", role: .cancel) {}
        } message: { Text("JARVIS stops until RESUME is pressed on the PC.") }
        .onAppear { session.prepareMicrophone() }   // the health polling is owned by MainTabs
    }

    // MARK: the core

    private var stateWord: String {
        switch session.state {
        case .offline: return "Not reached"
        case .idle: return "Core online"
        case .listening: return "Listening"
        case .thinking: return "Thinking"
        case .executing: return "Working"
        case .speaking: return "Speaking"
        case .stopped: return "Emergency stop"
        case .error: return "Not answered"
        }
    }

    private var stateColor: Color {
        switch session.state {
        case .offline: return Theme.muted
        case .listening: return Theme.good
        case .thinking, .executing: return Theme.warn
        case .stopped, .error: return Theme.bad
        default: return Theme.good
        }
    }

    private var corePanel: some View {
        HudPanel(title: "JARVIS Core", status: stateWord, statusColor: stateColor) {
            VStack(spacing: 8) {
                CoreOrb(state: session.state, level: session.micLevels.last ?? 0)
                    .frame(height: 220)
                    .frame(maxWidth: .infinity)
                HStack(spacing: 14) {
                    // The release id as the Core sends it (a caption would upper-case it).
                    Text("Core \(session.metrics?.coreVersion ?? "—")").font(Theme.mono(10)).foregroundStyle(Theme.text).lineLimit(1)
                    Caption("Up \(Self.uptime(session.metrics?.coreUptimeSeconds))", size: 9)
                }
            }
            .frame(maxWidth: .infinity)
        }
    }

    // MARK: the six systems

    private struct SystemRow: Identifiable {
        let id: String
        let name: String
        let ready: Bool?
        let word: String
    }

    private var systems: [SystemRow] {
        let microphone = session.info?.allows(.microphone) ?? false
        let speakers = session.info?.allows(.speakers) ?? false
        let ai: Bool? = session.metrics?.aiReady
        return [
            SystemRow(id: "link", name: "Core link", ready: session.reached, word: session.reached ? "Online" : "Not reached"),
            SystemRow(id: "ai", name: "Core AI", ready: ai, word: ai.map { $0 ? "Ready" : "No key" } ?? "Not read"),
            SystemRow(id: "speech", name: "Speech recognition", ready: microphone, word: microphone ? "Allowed" : "Off"),
            SystemRow(id: "voice", name: "Voice", ready: speakers, word: speakers ? "Allowed" : "Off"),
            SystemRow(id: "stop", name: "Emergency stop", ready: !session.stopped, word: session.stopped ? "Stopped" : "Clear"),
            SystemRow(id: "phone", name: "This phone", ready: session.paired, word: session.paired ? "Paired" : "Not paired"),
        ]
    }

    private var readyCount: Int { systems.filter { $0.ready == true }.count }

    private var systemsWord: (String, Color) {
        if !session.reached { return ("Core not reached", Theme.bad) }
        if readyCount == systems.count { return ("All systems nominal", Theme.good) }
        return ("\(readyCount) of \(systems.count) ready", Theme.warn)
    }

    private var systemStatusPanel: some View {
        HudPanel(title: "System status", status: systemsWord.0, statusColor: systemsWord.1) {
            HStack(alignment: .center, spacing: 14) {
                VStack(alignment: .leading, spacing: 8) {
                    ForEach(systems) { row in
                        HStack(spacing: 8) {
                            StatusDot(color: row.ready == nil ? Theme.muted : (row.ready! ? Theme.good : Theme.bad))
                            Caption(row.name, color: Theme.text, size: 9).lineLimit(1)
                            Spacer(minLength: 6)
                            Caption(row.word, color: row.ready == nil ? Theme.muted : (row.ready! ? Theme.good : Theme.bad), size: 9)
                                .lineLimit(1)
                        }
                        .accessibilityElement(children: .combine)
                    }
                }
                ZStack {
                    ProgressRing(share: Double(readyCount) / Double(systems.count),
                                 color: session.reached ? (readyCount == systems.count ? Theme.good : Theme.warn) : Theme.bad)
                    VStack(spacing: 2) {
                        Text("\(readyCount)/\(systems.count)").font(.system(size: 18, weight: .light)).monospacedDigit().foregroundStyle(Theme.text)
                        Caption("Ready", size: 9)
                    }
                }
                .frame(width: 84, height: 84)
                .accessibilityElement(children: .ignore)
                .accessibilityLabel("\(readyCount) of \(systems.count) systems ready")
            }
        }
    }

    // MARK: live diagnostics

    private var sampledWord: String {
        guard let metrics = session.metrics else { return "Not read yet" }
        return "Sampled \(Date(timeIntervalSince1970: metrics.sampledAt).formatted(date: .omitted, time: .standard))"
    }

    private var diagnosticsPanel: some View {
        HudPanel(title: "Live diagnostics", status: sampledWord, statusColor: session.metrics == nil ? Theme.muted : Theme.accent) {
            VStack(alignment: .leading, spacing: 8) {
                LazyVGrid(columns: [GridItem(.flexible(), spacing: 8), GridItem(.flexible(), spacing: 8)], spacing: 8) {
                    DiagnosticTile(label: "CPU", value: session.metrics?.cpuPercent, unit: "%", history: session.healthHistory.compactMap(\.cpu))
                    DiagnosticTile(label: "Memory", value: session.metrics?.memory?.usedPercent, unit: "%", history: session.healthHistory.compactMap(\.memory))
                    DiagnosticTile(label: "Storage", value: session.metrics?.disk?.usedPercent, unit: "%", history: session.healthHistory.compactMap(\.disk))
                    DiagnosticTile(label: "Link", value: session.roundTripMs.map(Double.init), unit: "ms", history: session.healthHistory.compactMap(\.link))
                }
                HStack(spacing: 14) {
                    if let ms = session.metrics?.lastResponseMs {
                        Caption("Last reply \(String(format: "%.1f", ms / 1000)) s", size: 9)
                    }
                    Spacer(minLength: 0)
                }
                Text("CPU, memory and storage are read by the Core on the PC; link is this phone's round trip. Graphics, temperature, power and network traffic are not measured.")
                    .font(.system(size: 10)).foregroundStyle(Theme.muted.opacity(0.85))
            }
        }
    }

    // MARK: voice input

    private var voiceWord: (String, Color) {
        switch session.state {
        case .listening: return ("Listening", Theme.good)
        case .thinking: return ("Thinking", Theme.warn)
        case .executing: return ("Working", Theme.warn)
        case .speaking: return ("Speaking", Theme.good)
        case .stopped: return ("Stopped", Theme.bad)
        case .offline: return ("Not reached", Theme.muted)
        case .error: return ("Not answered", Theme.bad)
        case .idle: return ("Standing by", Theme.accent)
        }
    }

    private var voiceHint: String {
        if session.recording { return String(format: "%.0f s of 30", session.recordingSeconds) }
        if session.stopped { return "RESUME on the PC." }
        if !(session.info?.allows(.microphone) ?? false) { return "Microphone not allowed on the PC." }
        return "Hold to speak."
    }

    private var voicePanel: some View {
        HudPanel(title: "Voice input", status: voiceWord.0, statusColor: voiceWord.1) {
            VStack(alignment: .leading, spacing: 8) {
                HStack(spacing: 12) {
                    HoldToSpeakButton()
                    VStack(alignment: .leading, spacing: 6) {
                        WaveformBars(levels: session.micLevels, color: session.recording ? Theme.good : Theme.accent)
                            .frame(height: 40)
                        Text(voiceHint).font(.system(size: 11)).foregroundStyle(Theme.muted).lineLimit(1)
                    }
                }
                if let held = session.held {
                    Text("Held until the Core is back: \(held.shown)")
                        .font(.system(size: 11)).foregroundStyle(Theme.warn).lineLimit(1)
                } else if let writing = session.writing {
                    Text("JARVIS (writing): \(writing)")
                        .font(.system(size: 11)).foregroundStyle(Theme.muted).lineLimit(1)
                } else if let last = session.lines.last {
                    Text("\(last.isUser ? "You" : "JARVIS"): \(last.text)")
                        .font(.system(size: 11)).foregroundStyle(Theme.muted).lineLimit(1)
                }
            }
        }
    }

    // MARK: projects and upcoming

    private var projectsPanel: some View {
        HudPanel(title: "Active projects",
                 status: session.overview.map { "\($0.projects.count) active · \($0.tasksOpen) open tasks" } ?? "Not read yet",
                 statusColor: session.overview == nil ? Theme.muted : Theme.accent) {
            if let overview = session.overview {
                if overview.projects.isEmpty {
                    Text("No projects on the PC.").font(.system(size: 11)).foregroundStyle(Theme.muted)
                } else {
                    let largest = max(1, overview.projects.map(\.openTasks).max() ?? 1)
                    VStack(spacing: 10) {
                        ForEach(overview.projects) { project in
                            HStack(spacing: 10) {
                                Image(systemName: "folder").font(.system(size: 12)).foregroundStyle(Theme.accent).frame(width: 16)
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(project.name).font(.system(size: 11.5, weight: .semibold)).foregroundStyle(Theme.text).lineLimit(1)
                                    GeometryReader { geo in
                                        ZStack(alignment: .leading) {
                                            Rectangle().fill(Theme.accent.opacity(0.14))
                                            Rectangle().fill(Theme.accent)
                                                .frame(width: geo.size.width * CGFloat(project.openTasks) / CGFloat(largest))
                                        }
                                    }
                                    .frame(height: 3)
                                }
                                Text(project.openTasks == 0 ? "none open" : "\(project.openTasks) open")
                                    .font(.system(size: 10)).monospacedDigit().foregroundStyle(Theme.muted).frame(width: 64, alignment: .trailing)
                            }
                            .accessibilityElement(children: .combine)
                        }
                    }
                }
            } else {
                Text("Not read yet.").font(.system(size: 11)).foregroundStyle(Theme.muted)
            }
        }
    }

    private var upcomingPanel: some View {
        HudPanel(title: "Upcoming",
                 status: session.overview.map { $0.reminders.isEmpty ? "Nothing in 24 h" : "\($0.reminders.count) in 24 h" } ?? "Not read yet",
                 statusColor: session.overview == nil ? Theme.muted : Theme.accent) {
            if let overview = session.overview {
                if overview.reminders.isEmpty {
                    Text("Nothing in the next 24 hours.").font(.system(size: 11)).foregroundStyle(Theme.muted)
                } else {
                    VStack(spacing: 8) {
                        ForEach(Array(overview.reminders.enumerated()), id: \.offset) { _, reminder in
                            HStack(spacing: 10) {
                                Text(Date(timeIntervalSince1970: reminder.due).formatted(date: .omitted, time: .shortened))
                                    .font(.system(size: 11)).monospacedDigit().foregroundStyle(Theme.accent).frame(width: 64, alignment: .leading)
                                Text(reminder.title).font(.system(size: 11)).foregroundStyle(reminder.fired ? Theme.muted : Theme.text).lineLimit(1)
                                Spacer()
                                if reminder.fired { Caption("Done", size: 9) }
                            }
                            .accessibilityElement(children: .combine)
                        }
                    }
                }
            } else {
                Text("Not read yet.").font(.system(size: 11)).foregroundStyle(Theme.muted)
            }
        }
    }

    // MARK: this phone

    private var phonePanel: some View {
        HudPanel(title: "This phone", status: session.paired ? "Paired" : "Not paired", statusColor: session.paired ? Theme.good : Theme.bad) {
            VStack(alignment: .leading, spacing: 6) {
                row("Connection", session.reached ? (session.roundTripMs.map { "Reached · \($0) ms round trip" } ?? "Reached") : "Not reached", good: session.reached)
                row("Address", session.address.map { "\($0.host):\($0.port)" } ?? "—", good: nil)
                row("Paired as", session.deviceName ?? "This phone", good: nil)
                row("May save", (session.info?.writes ?? false) ? "Memories and tasks (ticked on the PC)" : "Questions and reading only", good: nil)
                row("Device", "\(String(AppSettings.deviceId?.prefix(4) ?? ""))…\(String(AppSettings.deviceId?.suffix(4) ?? ""))", good: nil)
            }
        }
    }

    private func row(_ label: String, _ value: String, good: Bool?) -> some View {
        HStack(alignment: .firstTextBaseline, spacing: 8) {
            Caption(label, size: 9).frame(width: 84, alignment: .leading)
            Text(value).font(.system(size: 11)).foregroundStyle(Theme.text).lineLimit(1).minimumScaleFactor(0.82)   // never under 9 pt
            if let good {
                Image(systemName: good ? "checkmark" : "exclamationmark.triangle").font(.system(size: 9)).foregroundStyle(good ? Theme.good : Theme.bad)
            }
            Spacer(minLength: 0)
        }
        .accessibilityElement(children: .combine)
    }

    private var footer: some View {
        // Not a Caption: the release id keeps its case, as the Core sends it.
        Text("TEAGUE INDUSTRIES OS · JARVIS for iPhone \(AppInfo.version) · Core \(session.metrics?.coreVersion ?? "—")")
            .font(Theme.caption(9)).tracking(1.0).foregroundStyle(Theme.muted)
            .multilineTextAlignment(.center)
            .frame(maxWidth: .infinity)
            .padding(.top, 4)
    }

    static func uptime(_ seconds: Int?) -> String {
        guard let seconds else { return "—" }
        if seconds < 3600 { return "\(seconds / 60) min" }
        if seconds < 86400 { return "\(seconds / 3600) h \((seconds % 3600) / 60) min" }
        return "\(seconds / 86400) d \((seconds % 86400) / 3600) h"
    }
}
