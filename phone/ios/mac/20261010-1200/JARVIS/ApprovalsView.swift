import SwiftUI

/// Approve from the pocket (round 5, R1 of docs/MAC-REQUESTS-20261007.md): what waits for the owner's word on the
/// PC, with APPROVE behind Face ID and REJECT. Shown only when the owner has ticked "May approve for JARVIS" for
/// this phone on the PC; on an older Core it says so and shows nothing invented.
struct ApprovalsView: View {
    @EnvironmentObject private var session: SessionModel
    @Environment(\.dismiss) private var dismiss
    @State private var working: String?   // the item being answered

    var body: some View {
        NavigationStack {
            ZStack {
                PageBackground()
                ScrollView {
                    VStack(spacing: 12) {
                        switch session.approvalsAvailability {
                        case .unknown:
                            if let failure = session.approvalsFailure {
                                Text(failure).font(.system(size: 12)).foregroundStyle(Theme.warn).multilineTextAlignment(.center)
                            } else {
                                Text(session.reached ? "Reading…" : "The Core has not answered yet.").font(.system(size: 12)).foregroundStyle(Theme.muted)
                            }
                        case .notOnThisCore:
                            Panel(marked: false) {
                                Text("Approving from the phone needs JARVIS release 1.0.17 on the PC. This Core does not serve it yet.")
                                    .font(.system(size: 12)).foregroundStyle(Theme.muted)
                            }
                        case .notAllowed:
                            Panel(marked: false) {
                                Text("Approving is set on the PC: Settings > Devices > this phone > \"May approve for JARVIS\".")
                                    .font(.system(size: 12)).foregroundStyle(Theme.muted)
                            }
                        case .ready:
                            if let failure = session.approvalsFailure {   // a refresh that failed: the list below is the last one read
                                Text(failure).font(.system(size: 11)).foregroundStyle(Theme.warn).multilineTextAlignment(.center)
                            }
                            if session.approvals.isEmpty && session.approvalOutcomes.isEmpty {
                                Panel(marked: false) {
                                    Text("Nothing is waiting.").font(.system(size: 12)).foregroundStyle(Theme.muted)
                                }
                            }
                            ForEach(session.approvals) { item in card(item) }
                            // The receipts of the last answers, newest first, for items no longer listed.
                            ForEach(session.approvalOutcomes.filter { outcome in !session.approvals.contains { $0.id == outcome.id } }) { outcome in
                                Panel(marked: false) {
                                    HStack(alignment: .firstTextBaseline, spacing: 8) {
                                        if let symbol = symbol(for: outcome.kind) {
                                            Image(systemName: symbol).font(.system(size: 12)).foregroundStyle(outcome.kind == .applied ? Theme.good : Theme.bad)
                                        }
                                        VStack(alignment: .leading, spacing: 2) {
                                            Text(outcome.label).font(.system(size: 12, weight: .semibold)).foregroundStyle(Theme.text)
                                            Text(outcome.sentence).font(.system(size: 12)).foregroundStyle(Theme.muted)
                                        }
                                    }
                                }
                            }
                        }
                        if session.stopped {
                            Text("Emergency stop is on: nothing can be approved until RESUME is pressed on the PC.")
                                .font(.system(size: 11)).foregroundStyle(Theme.warn).multilineTextAlignment(.center)
                        }
                    }
                    .padding(16)
                }
                .refreshable { await session.loadApprovals() }
            }
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) { Button("Done") { dismiss() }.tint(Theme.accent) }
            }
            .toolbarBackground(Theme.ground2, for: .navigationBar)
            .navigationTitle("Approvals")
            .navigationBarTitleDisplayMode(.inline)
        }
        .task { await session.loadApprovals() }
        // The list follows the Core: a new item waiting, one answered on the PC, or the hello arriving after the sheet opened.
        .onChange(of: session.waitingApprovals) { _, _ in Task { await session.loadApprovals() } }
        .onChange(of: session.info?.servesApprovals) { _, _ in Task { await session.loadApprovals() } }
        // After RESUME on the PC the list is read again (the stop dropped what waited; new items may come).
        .onChange(of: session.stopped) { _, on in if !on { Task { await session.loadApprovals() } } }
    }

    private func symbol(for kind: ApprovalOutcome.Kind) -> String? {
        switch kind {
        case .applied: return "checkmark.seal"
        case .denied, .failed: return "xmark.circle"
        case .error: return nil
        }
    }

    private func card(_ item: ApprovalItem) -> some View {
        Panel {
            VStack(alignment: .leading, spacing: 8) {
                HStack(alignment: .firstTextBaseline) {
                    Caption(kindWord(item.kind), color: Theme.accent, size: 9)
                    Spacer()
                    Caption(expiry(item), size: 9)
                }
                Text(item.label).font(.system(size: 14, weight: .semibold)).foregroundStyle(Theme.text)
                Text("From \(item.deviceName) · \(Date(timeIntervalSince1970: item.created).formatted(date: .omitted, time: .shortened))")
                    .font(.system(size: 11)).foregroundStyle(Theme.muted)
                if !item.detail.isEmpty {
                    // A self-change's difference keeps its lines (two-way scroll); any other detail wraps.
                    ScrollView(item.kind == "self_change" ? [.vertical, .horizontal] : .vertical) {
                        Text(item.detail).font(Theme.mono(10)).foregroundStyle(Theme.text.opacity(0.9))
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                    .frame(maxHeight: item.kind == "self_change" ? 240 : 120)
                    .padding(8)
                    .background(Theme.ground2.opacity(0.6))
                    .overlay(Rectangle().stroke(Theme.accent.opacity(0.18), lineWidth: 1))
                }
                if let outcome = session.approvalOutcomes.first(where: { $0.id == item.id }) {
                    Text(outcome.sentence).font(.system(size: 11)).foregroundStyle(Theme.warn)   // an error while the item still waits
                }
                HStack(spacing: 10) {
                    Button {
                        working = item.id
                        Task { await session.reject(item); working = nil }
                    } label: {
                        Text("REJECT").font(Theme.caption(10)).tracking(1.2).foregroundStyle(Theme.bad)
                            .frame(maxWidth: .infinity).frame(height: 44)
                            .overlay(Rectangle().stroke(Theme.bad.opacity(0.6), lineWidth: 1))
                    }
                    .disabled(working != nil)
                    .accessibilityLabel("Reject: \(item.label)")
                    if !session.stopped {
                        Button {
                            working = item.id
                            Task { await session.approve(item); working = nil }
                        } label: {
                            HStack(spacing: 6) {
                                Image(systemName: "faceid").font(.system(size: 13))
                                Text("APPROVE").font(Theme.caption(10)).tracking(1.2)
                            }
                            .foregroundStyle(Theme.ground2)
                            .frame(maxWidth: .infinity).frame(height: 44)
                            .background(Theme.accent)
                        }
                        .disabled(working != nil)
                        .accessibilityLabel("Approve with Face ID: \(item.label)")
                    }
                }
            }
        }
    }

    private func kindWord(_ kind: String) -> String {
        switch kind {
        case "tool": return "A tool set to ask first"
        case "memory": return "A memory"
        case "self_change": return "JARVIS's change to itself"
        case "draft": return "A drafted action"
        default: return kind
        }
    }

    private func expiry(_ item: ApprovalItem) -> String {
        let left = item.expires - Date().timeIntervalSince1970
        if left <= 0 { return "Expired" }
        if left < 60 { return "Expires in under a minute" }
        return "Expires in \(Int(left / 60)) min"
    }
}

/// The notices the Core has for this phone (round 5, R4): nudges, announcements, waiting approvals, system notes.
struct NoticesView: View {
    @EnvironmentObject private var session: SessionModel
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            ZStack {
                PageBackground()
                ScrollView {
                    VStack(spacing: 10) {
                        switch session.noticesAvailability {
                        case .unknown:
                            // A failed first read says why, instead of an endless "Reading…". (Notices answer as usual
                            // while the emergency stop holds: MAC-BRIEF-20261010.md section 2, item 10.)
                            Text(session.noticesFailure ?? "Reading…")
                                .font(.system(size: 12)).foregroundStyle(session.noticesFailure != nil ? Theme.warn : Theme.muted)
                                .multilineTextAlignment(.center)
                        case .notOnThisCore:
                            Panel(marked: false) {
                                Text("Notices need JARVIS release 1.0.17 on the PC. This Core does not serve them yet.")
                                    .font(.system(size: 12)).foregroundStyle(Theme.muted)
                            }
                        case .notAllowed, .ready:
                            if let failure = session.noticesFailure {   // a refresh that failed: the list below is the last one read
                                Text(failure).font(.system(size: 11)).foregroundStyle(Theme.warn).multilineTextAlignment(.center)
                            }
                            if session.noticeItems.isEmpty {
                                Panel(marked: false) { Text("No notices.").font(.system(size: 12)).foregroundStyle(Theme.muted) }
                            }
                            ForEach(session.noticeItems) { item in
                                Panel(marked: false) {
                                    VStack(alignment: .leading, spacing: 4) {
                                        HStack {
                                            Caption(kindWord(item.kind), color: Theme.accent, size: 9)
                                            Spacer()
                                            Caption(Date(timeIntervalSince1970: item.created).formatted(date: .abbreviated, time: .shortened), size: 9)
                                        }
                                        Text(item.text).font(.system(size: 13)).foregroundStyle(Theme.text)
                                    }
                                }
                            }
                        }
                    }
                    .padding(16)
                }
                .refreshable { await session.loadNotices() }
            }
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) { Button("Done") { dismiss() }.tint(Theme.accent) }
            }
            .toolbarBackground(Theme.ground2, for: .navigationBar)
            .navigationTitle("Notices")
            .navigationBarTitleDisplayMode(.inline)
        }
        .task { await session.loadNotices() }
    }

    private func kindWord(_ kind: String) -> String {
        switch kind {
        case "nudge": return "Nudge"
        case "announce": return "Announcement"
        case "approval": return "Waiting for approval"
        case "system": return "From the Core"
        default: return kind
        }
    }
}
