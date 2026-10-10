import SwiftUI

/// "What can I say?" (round 6, item 10): the phrases, buttons and set-ups of the app in one place, opened from Phone
/// settings. Words only; nothing here reads or changes anything.
struct HelpView: View {
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            ZStack {
                PageBackground()
                ScrollView {
                    VStack(spacing: 12) {
                        section("Talk to JARVIS", [
                            "Tap the microphone once for a conversation: JARVIS listens, sends your words when you pause, answers, and listens again.",
                            "Say \"thank you Jarvis\", \"stop listening\" or \"that's all\" to end it, or tap the microphone. A request that ends with those words (\"lights off, thank you Jarvis\") is answered first. It also ends after 20 seconds of silence, after three turns in a row with nothing understood, when you leave the app or lock the phone, and at the first turn after ten minutes.",
                            "While JARVIS speaks, tap the microphone to skip to your turn.",
                            "For a single question, hold the microphone, speak, and let go to send."
                        ])
                        section("Siri", [
                            "\"Hey Siri, ask JARVIS\": Siri asks what to ask, and says JARVIS's reply right there, without opening the app. The iPhone must be unlocked (from the lock screen Siri asks for Face ID first), and Lock with Face ID in Phone settings must be off: while it is on, Siri says so and the app asks instead. The question and the reply go into your conversation on Ask (or, while the app is still busy with a question of its own, into a new one in Chats). Siri waits about 25 seconds; a longer answer is in the app.",
                            "\"Hey Siri, talk to JARVIS\": a conversation, in the app.",
                            "\"Hey Siri, send an announcement to JARVIS\": Siri asks who it is from and what it says, and the PC reads it out.",
                            "\"Hey Siri, stop JARVIS\": the emergency stop. Only RESUME on the PC lifts it."
                        ])
                        section("Without opening the app", [
                            "Siri: \"Hey Siri, ask JARVIS\" answers without the app (above; Lock with Face ID off).",
                            "Share to JARVIS answers inside the share sheet (below).",
                            "A shortcut: Shortcuts app > + > add Dictate Text, then Ask JARVIS (its question: Dictated Text), then Speak Text (JARVIS's reply). Set that shortcut as a Back Tap and a double tap on the back of the phone asks JARVIS, no app needed (with Lock with Face ID off, as for Siri).",
                            "The widget: touch and hold the Home Screen, tap Edit > Add Widget, and choose JARVIS. It shows whether JARVIS is online or stopped and how many approvals and notices wait for you; on the medium size a tap on a count opens that list. iPhone refreshes it now and then (about every 15 minutes at best), and sooner when the app sees a change.",
                            "The Ask JARVIS button: in Control Center or on the lock screen, tap Edit or Customise, then Add a Control, and choose JARVIS. A press opens the app in a conversation.",
                            "Back Tap for a conversation: iPhone Settings > Accessibility > Touch > Back Tap > Double Tap, and choose Talk to JARVIS. If it is not in the list, first make a shortcut: Shortcuts app > + > Add Action > search JARVIS > Talk to JARVIS > Done, then choose that shortcut in Back Tap."
                        ])
                        section("Look at this", [
                            "Tap Look at this above the buttons, take a photo or choose one, and ask about it.",
                            "It needs the camera ticked for this phone on the PC: Settings > Devices > this phone > camera. The picture goes to your PC and, from there, to JARVIS's AI provider."
                        ])
                        section("Share to JARVIS", [
                            "In Safari, Photos, Notes and most apps: Share > JARVIS (if it is not in the row, More > JARVIS). Say what you want done with it and tap Send. The reply shows there and stays in Chats; you can ask more about it in the same sheet.",
                            "From Safari the page's text goes with your question (the first 11,000 characters or so of a long page), so JARVIS can summarise it. A picture needs the camera ticked for this phone on the PC, as for Look at this."
                        ])
                        section("Your texts, read out on the PC", [
                            "iPhone lets no app read your texts, so one Shortcuts automation per person does it:",
                            "Shortcuts app > Automation > + > Message. Sender: the person. Run Immediately, Notify When Run off. Next > New Blank Automation > add Announce to JARVIS. From: the person's name. Message: Shortcut Input. Done.",
                            "When that person texts, the PC says it aloud and the phone lists it under Notices."
                        ])
                        section("Replies and chats", [
                            "Tap a JARVIS reply to hear it again. Press and hold any line to copy or share it.",
                            "In Chats, open a conversation and tap Share to send it as text (its last 100 lines)."
                        ])
                        section("Approvals", [
                            "When something waits for your word, \"1 approval waiting\" shows on Ask and a notice pops up under the header. APPROVE asks Face ID first; REJECT does not."
                        ])
                    }
                    .padding(16)
                }
            }
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) { Button("Done") { dismiss() }.tint(Theme.accent) }
                ToolbarItem(placement: .topBarLeading) { SheetStopButton() }   // the emergency stop on every screen
            }
            .toolbarBackground(Theme.ground2, for: .navigationBar)
            .navigationTitle("What can I say?")
            .navigationBarTitleDisplayMode(.inline)
        }
    }

    private func section(_ title: String, _ lines: [String]) -> some View {
        HudPanel(title: title) {
            VStack(alignment: .leading, spacing: 8) {
                ForEach(Array(lines.enumerated()), id: \.offset) { _, line in
                    Text(line).font(.system(size: 13)).foregroundStyle(Theme.text.opacity(0.92))
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
        }
    }
}
