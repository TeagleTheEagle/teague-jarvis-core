import XCTest

/// The round 2 phone checks, driven from the Mac on the owner's paired iPhone (RESULTS.md). Run with
/// `xcodebuild test -scheme JARVIS-PhoneChecks -destination 'id=<udid>'`; every step leaves a full-screen
/// screenshot and a note in the result bundle (`xcrun xcresulttool export attachments`).
///
/// The tests touch only the app's own controls: the three tabs, the Voice button, the type field and Send, the
/// settings sheet. They never press STOP ALL (that raises the emergency stop on the Core, and only the PC lifts it).
/// `test4_FaceIDLockScreen` turns the Face ID lock ON and leaves it on: the owner's face is the only way through it
/// afterwards, so run it only when the owner has said so.
final class PhoneChecksUITests: XCTestCase {
    private var app: XCUIApplication!

    override func setUpWithError() throws {
        continueAfterFailure = true
        app = XCUIApplication()
    }

    // MARK: helpers

    private func shot(_ name: String) {
        let attachment = XCTAttachment(screenshot: XCUIScreen.main.screenshot())
        attachment.name = name
        attachment.lifetime = .keepAlways
        add(attachment)
    }

    private func note(_ text: String) {
        let attachment = XCTAttachment(string: text)
        attachment.name = "note"
        attachment.lifetime = .keepAlways
        add(attachment)
        NSLog("PHONECHECK %@", text)
    }

    private func tab(_ name: String) -> XCUIElement {
        let inBar = app.tabBars.buttons[name].firstMatch
        return inBar.exists ? inBar : app.buttons[name].firstMatch
    }

    private var stopButton: XCUIElement {
        let live = app.buttons["Emergency stop: stop everything"].firstMatch
        return live.exists ? live : app.buttons["Emergency stop is on"].firstMatch
    }

    private func openOnTheScreens() {
        app.launch()
        XCTAssertTrue(tab("Ask").waitForExistence(timeout: 25), "the three screens did not appear (not paired, or the lock is on)")
    }

    /// The number of long texts on screen: a rough count of the conversation's lines.
    private func transcriptCount() -> Int {
        app.staticTexts.allElementsBoundByIndex.filter { $0.label.count > 25 }.count
    }

    /// Check 2: ONLINE on one line and STOP ALL readable, on the screen named. The title JARVIS must keep its room
    /// too (the run of 2026-10-07 00:45 showed "JA…" beside a long state word). Chats has no state word.
    private func checkHeader(_ screen: String, expectsStateWord: Bool = true) {
        XCTAssertTrue(stopButton.waitForExistence(timeout: 8), "\(screen): no STOP ALL button in the header")
        let stopFrame = stopButton.frame
        XCTAssertGreaterThan(stopFrame.width, 70, "\(screen): STOP ALL is squeezed (\(Int(stopFrame.width)) pt wide)")
        let title = app.staticTexts["JARVIS"].firstMatch
        XCTAssertTrue(title.waitForExistence(timeout: 3), "\(screen): the title JARVIS is missing in the header")
        // A cut title keeps its full accessibility label, so the width is the real test (about 85 % of 20 pt JARVIS).
        XCTAssertGreaterThan(title.frame.width, 55, "\(screen): the title JARVIS is cut (\(Int(title.frame.width)) pt wide)")
        note("\(screen): title JARVIS \(Int(title.frame.width)) pt wide")
        let words = app.staticTexts.allElementsBoundByIndex
            .filter { $0.frame.maxY < 140 }
            .map { "\($0.label) \(Int($0.frame.width))x\(Int($0.frame.height))" }
        guard expectsStateWord else {
            note("\(screen): header texts: \(words.joined(separator: " | ")); STOP ALL \(Int(stopFrame.width))x\(Int(stopFrame.height)) pt")
            return
        }
        let online = app.staticTexts["ONLINE"].firstMatch
        if online.waitForExistence(timeout: 12) {
            XCTAssertLessThan(online.frame.height, 26, "\(screen): ONLINE wraps onto two lines (\(Int(online.frame.height)) pt tall)")
            note("\(screen): ONLINE \(Int(online.frame.width))x\(Int(online.frame.height)) pt; STOP ALL \(Int(stopFrame.width))x\(Int(stopFrame.height)) pt")
        } else {
            note("\(screen): ONLINE not shown; header texts: \(words.joined(separator: " | "))")
            XCTFail("\(screen): the Core was not reached from the phone, so ONLINE could not be checked (Tailscale on the phone and the PC? JARVIS running on the PC?)")
        }
    }

    /// The Core's own sentence when it cannot be reached, as the Ask screen shows it.
    private var coreNotReached: Bool {
        app.staticTexts["CORE NOT REACHED"].firstMatch.exists
            || app.staticTexts.matching(NSPredicate(format: "label CONTAINS 'cannot be reached'")).firstMatch.exists
    }

    // MARK: the checks

    /// Check 2 on every screen.
    func test1_HeaderOnEveryScreen() {
        openOnTheScreens()
        sleep(1)
        shot("ask")
        checkHeader("Ask")
        tab("Chats").tap()
        sleep(1)
        shot("chats")
        checkHeader("Chats", expectsStateWord: false)
        tab("Overview").tap()
        sleep(1)
        shot("overview")
        checkHeader("Overview")
        // The rest of the Overview's panels, two screens down.
        let scroll = app.scrollViews.firstMatch
        if scroll.exists {
            scroll.swipeUp()
            sleep(1)
            shot("overview-2")
            scroll.swipeUp()
            sleep(1)
            shot("overview-3")
        }
        tab("Ask").tap()
    }

    /// Check 6, the button half: the Voice button changes between spoken and muted and back.
    func test2_VoiceButton() {
        openOnTheScreens()
        tab("Ask").tap()
        let spoken = app.buttons["Replies are spoken. Tap to mute them"].firstMatch
        let silent = app.buttons["Replies are silent. Tap to speak them"].firstMatch
        XCTAssertTrue(spoken.waitForExistence(timeout: 5) || silent.exists, "no Voice button beside the microphone")
        let wasSpoken = spoken.exists
        note("voice at start: \(wasSpoken ? "on" : "muted")")
        (wasSpoken ? spoken : silent).tap()
        XCTAssertTrue((wasSpoken ? silent : spoken).waitForExistence(timeout: 4), "the Voice button did not change after a tap")
        shot(wasSpoken ? "voice-muted" : "voice-on")
        (wasSpoken ? silent : spoken).tap()
        XCTAssertTrue((wasSpoken ? spoken : silent).waitForExistence(timeout: 4), "the Voice button did not change back")
        shot(wasSpoken ? "voice-on-again" : "voice-muted-again")
    }

    /// A typed question answered by the Core: the round trip of the round 2 build, with the working state seen.
    func test3_TypedQuestionAnswered() {
        openOnTheScreens()
        tab("Ask").tap()
        let before = transcriptCount()
        app.buttons["Type a request"].firstMatch.tap()
        let field = app.textFields.firstMatch
        XCTAssertTrue(field.waitForExistence(timeout: 5), "the type field did not open")
        field.tap()
        field.typeText("What time is it in Sydney right now? One short sentence, please.")
        let send = app.buttons["Send"].firstMatch
        XCTAssertTrue(send.waitForExistence(timeout: 3), "no Send button")
        send.tap()
        shot("question-sent")
        let working = app.buttons["Cancel this question"].firstMatch
        let idle = app.buttons["New conversation"].firstMatch
        let sawWorking = working.waitForExistence(timeout: 10)
        note("working state shown: \(sawWorking)")
        if sawWorking { shot("working") }
        XCTAssertTrue(idle.waitForExistence(timeout: 90), "no reply within 90 s")
        sleep(2)
        shot("reply")
        let after = transcriptCount()
        note("long texts on screen before \(before), after \(after)")
        XCTAssertFalse(coreNotReached, "the Core was not reached from the phone: the question was shown but not answered")
        XCTAssertGreaterThan(after, before + 1, "no reply line on screen after the question (only the question itself)")
    }

    // MARK: round 5 against Core 1.0.17 (docs/PC-BRIEF-20261010.md section 3, step 4)

    /// Open the app and wait for the owner's face: the Face ID lock stays on, so the screens come only after it.
    private func openAfterFaceID() {
        app.launch()
        note("waiting up to 90 s for the owner's Face ID")
        XCTAssertTrue(tab("Ask").waitForExistence(timeout: 90), "the screens did not appear within 90 s (Face ID not passed?)")
        sleep(2)
    }

    /// What one typed question gave.
    private struct Asked {
        var reached: Bool
        var reply: String
    }

    /// Type a question on Ask, send it, wait for the reply (up to `timeout` seconds), and note the reply's words.
    /// Waits for a spoken reply to finish first, so no reply is cut off. When the Core cannot be reached the
    /// question is held on the phone: the caller stops there instead of piling up questions.
    @discardableResult
    private func ask(_ question: String, shotName: String, timeout: TimeInterval = 150) -> Asked {
        if tab("Ask").isHittable { tab("Ask").tap() }
        let idle = app.buttons["New conversation"].firstMatch
        XCTAssertTrue(idle.waitForExistence(timeout: 30), "\(shotName): JARVIS was still busy with something else")
        let speaking = app.staticTexts["SPEAKING"].firstMatch
        if speaking.exists {
            let gone = NSPredicate(format: "exists == false")
            _ = XCTWaiter.wait(for: [expectation(for: gone, evaluatedWith: speaking)], timeout: 90)
        }
        let field = app.textFields.firstMatch
        if !field.exists { app.buttons["Type a request"].firstMatch.tap() }   // the button opens and closes the bar
        XCTAssertTrue(field.waitForExistence(timeout: 5), "\(shotName): the type field did not open")
        field.tap()
        field.typeText(question)
        app.buttons["Send"].firstMatch.tap()
        let working = app.buttons["Cancel this question"].firstMatch.waitForExistence(timeout: 10)
        // The reply being written (Core 1.0.17, when the PC's "Show replies while they are written" is on).
        let draft = app.otherElements.matching(NSPredicate(format: "label BEGINSWITH 'JARVIS is writing'")).firstMatch
        var writing = false
        let until = Date().addingTimeInterval(timeout)
        while Date() < until {
            if !writing, draft.exists { writing = true; shot("\(shotName)-writing") }
            if idle.exists { break }
            usleep(500_000)
        }
        XCTAssertTrue(idle.exists, "\(shotName): no reply within \(Int(timeout)) s")
        // The bar closed again, so the keyboard covers neither the tabs nor the waiting line.
        if field.exists { app.buttons["Type a request"].firstMatch.tap() }
        sleep(2)
        // The reply is the text after the question in the conversation; the screen is scrolled down to it.
        let texts = app.staticTexts.allElementsBoundByIndex.map(\.label)
        var reply = ""
        if let at = texts.lastIndex(of: question), at + 1 < texts.count { reply = texts[at + 1] }
        let scroll = app.scrollViews.firstMatch
        if scroll.exists { scroll.swipeUp(); usleep(500_000) }
        shot(shotName)
        let reached = !coreNotReached
        note("\(shotName): working shown \(working); reply written live \(writing); Core reached \(reached); reply: \(reply.prefix(700))")
        if scroll.exists { scroll.swipeDown(); usleep(300_000) }
        return Asked(reached: reached, reply: reply)
    }

    /// The Core could not be reached: the question the phone now holds is dropped, so it is never sent later on its
    /// own (a timer, a memory), and the test stops there.
    private func stopHere() {
        let drop = app.buttons["Drop the held question"].firstMatch
        if drop.exists { drop.tap(); note("the held question was dropped") }
        XCTFail("the Core was not reached from the phone: stopped here")
    }

    /// This phone's name as the Core knows it (THIS PHONE's "Paired as" row on the Overview), or nil.
    private func pairedName() -> String? {
        tab("Overview").tap()
        let scroll = app.scrollViews.firstMatch
        for _ in 0..<4 { scroll.swipeUp(); usleep(400_000) }
        sleep(1)
        let texts = app.staticTexts.allElementsBoundByIndex.map(\.label)
        let combined = app.descendants(matching: .any).matching(NSPredicate(format: "label BEGINSWITH[c] 'PAIRED AS, '")).firstMatch
        let combinedLabel = combined.exists ? combined.label : nil
        tab("Ask").tap()
        // The row may come as two texts ("PAIRED AS", the name) or as one combined element ("PAIRED AS, <name>").
        if let at = texts.firstIndex(where: { $0.uppercased() == "PAIRED AS" }), at + 1 < texts.count {
            let name = texts[at + 1].trimmingCharacters(in: .whitespaces)
            if !name.isEmpty { return name }
        }
        if let label = combinedLabel {
            let name = String(label.dropFirst("PAIRED AS, ".count)).trimmingCharacters(in: .whitespaces)
            if !name.isEmpty { return name }
        }
        return nil
    }

    /// The texts on screen that contain `word`, for the notes.
    private func lines(containing word: String) -> [String] {
        app.staticTexts.matching(NSPredicate(format: "label CONTAINS[c] %@", word)).allElementsBoundByIndex.map(\.label)
    }

    /// The Overview's bottom panels (THIS PHONE with the location row, the device ecosystem), noted and photographed.
    private func noteOverviewBottom(_ shotName: String) {
        tab("Overview").tap()
        let scroll = app.scrollViews.firstMatch
        for _ in 0..<4 { scroll.swipeUp(); usleep(400_000) }
        sleep(1)
        shot(shotName)
        note("\(shotName): location row: \(lines(containing: "sent").joined(separator: " | ")) ; devices: \(lines(containing: "device list").joined(separator: " | "))")
        tab("Ask").tap()
    }

    /// R2 (the scope sentence), R3 (location with a question), R7 (the PC's screen), "remember that" and R6. Starts a
    /// new conversation so the owner's own stays as it was; puts the location switch back as it was, even when the
    /// run is cut short. Saves one harmless memory on the PC ("remember that").
    func test5_Round5WithoutApproval() {
        openAfterFaceID()
        // The Core's uptime at the top of the Overview: whether JARVIS on the PC restarted since the last reading.
        tab("Overview").tap()
        sleep(3)
        shot("overview-top-uptime")
        note("uptime: \(lines(containing: "UP ").joined(separator: " | ")) ; core: \(lines(containing: "Core 1.0").joined(separator: " | "))")
        tab("Ask").tap()
        app.buttons["New conversation"].firstMatch.tap()
        sleep(1)

        // R2: the ticks and the scope sentence, in Phone settings.
        app.buttons["Phone settings"].firstMatch.tap()
        let location = app.switches.matching(NSPredicate(format: "label BEGINSWITH 'Send my location with questions'")).firstMatch
        XCTAssertTrue(location.waitForExistence(timeout: 5), "no location switch in Phone settings")
        shot("r2-settings-scope")
        note("scope lines: \(app.staticTexts.allElementsBoundByIndex.map(\.label).filter { $0.count > 30 }.prefix(4).joined(separator: " | "))")

        // R3: the location switch on (iOS asks only if it never has; the owner answers that).
        let wasOn = (location.value as? String) == "1"
        note("location switch at start: \(wasOn ? "on" : "off")")
        if !wasOn {
            location.tap()
            addTeardownBlock { [app] in
                // Back to off however the run ends, so the owner's location is never left on by a test.
                guard let app else { return }
                if app.state != .runningForeground { app.activate() }
                if !app.switches.matching(NSPredicate(format: "label BEGINSWITH 'Send my location with questions'")).firstMatch.exists {
                    if app.buttons["Done"].firstMatch.exists { app.buttons["Done"].firstMatch.tap() }
                    app.buttons["Phone settings"].firstMatch.tap()
                }
                let back = app.switches.matching(NSPredicate(format: "label BEGINSWITH 'Send my location with questions'")).firstMatch
                if back.waitForExistence(timeout: 5), (back.value as? String) == "1" { back.tap() }
                if app.buttons["Done"].firstMatch.exists { app.buttons["Done"].firstMatch.tap() }
            }
        }
        let springboard = XCUIApplication(bundleIdentifier: "com.apple.springboard")
        if springboard.alerts.firstMatch.waitForExistence(timeout: 4) {
            note("iOS asks about location: waiting up to 60 s for the owner's answer")
            shot("r3-ios-location-question")
            let gone = NSPredicate(format: "exists == false")
            _ = XCTWaiter.wait(for: [expectation(for: gone, evaluatedWith: springboard.alerts.firstMatch)], timeout: 60)
        }
        sleep(1)
        shot("r3-location-switch-on")
        app.buttons["Done"].firstMatch.tap()
        sleep(12)   // a first fix
        noteOverviewBottom("r3-r6-overview-bottom")
        guard ask("Using my location, which suburb am I in, and how far is the nearest train station? Two short sentences.", shotName: "r3-location-answer").reached else {
            return stopHere()
        }

        // R7: the PC's screen from the phone.
        guard ask("Analyse my screen.", shotName: "r7-analyse-screen").reached else {
            return stopHere()
        }

        // "Remember that" saves the line before it (Core 1.0.17).
        guard ask("Phone check note: the round 5 tests ran from the Mac on 10 October 2026.", shotName: "remember-1-line").reached else {
            return stopHere()
        }
        guard ask("Remember that", shotName: "remember-2-saved").reached else {
            return stopHere()
        }

        // The location still sent minutes later, with the phone sitting still (review of 2026-10-10, finding 3).
        noteOverviewBottom("r3-overview-later")
    }

    /// R1, APPROVE: a timer set to Ask first on the PC waits; APPROVE (with the owner's Face ID) carries it out.
    /// Needs the PC's Settings > Permissions > "Set a timer" on Ask first. Sets one real one-minute timer on the PC.
    func test6_Round5Approve() { approvalCheck(approving: true) }

    /// R1, REJECT: the same, answered with REJECT (no Face ID); no timer is set.
    func test7_Round5Reject() { approvalCheck(approving: false) }

    /// Ask for a one-minute timer and answer it. Answers only a waiting timer raised by this phone's own question,
    /// and only when it is the one item waiting: nothing else is ever answered by the test, least of all with the
    /// owner's face.
    private func approvalCheck(approving: Bool) {
        let tag = approving ? "r1-approve" : "r1-reject"
        openAfterFaceID()
        tab("Ask").tap()
        // Plan check 3 against 1.0.17: after the relaunch the last conversation's lines are read back from the Core.
        // A long text that is a conversation line: not the offline hint or a notice, and only with the Core reached.
        let hints = ["Tailscale on", "cannot be reached", "Hold the microphone", "held on this phone", "connection dropped"]
        func conversationLines() -> [String] {
            app.staticTexts.allElementsBoundByIndex.map(\.label)
                .filter { label in label.count > 40 && !hints.contains(where: { label.contains($0) }) }
        }
        var restored = false
        let readBy = Date().addingTimeInterval(20)
        while Date() < readBy, !restored {
            restored = !coreNotReached && !conversationLines().isEmpty
            if !restored { sleep(1) }
        }
        let scroll = app.scrollViews.firstMatch
        if scroll.exists { scroll.swipeUp(); usleep(500_000) }
        shot("\(tag)-restored-lines")
        note("\(tag): lines restored after the relaunch: \(restored); \(conversationLines().suffix(3).joined(separator: " | "))")
        if scroll.exists { scroll.swipeDown(); usleep(300_000) }
        app.buttons["New conversation"].firstMatch.tap()
        let open = app.buttons["Open approvals"].firstMatch
        // Only an item raised by this phone's own question is ever answered: its sheet line reads "From <name> · ...".
        guard let phone = pairedName() else {
            return XCTFail("this phone's paired name could not be read from the Overview; nothing is answered")
        }
        note("this phone is paired as \(phone)")
        // Anything already waiting (raised on the PC or by another question): answered on the PC, not by this test.
        if open.waitForExistence(timeout: 12) {
            shot("\(tag)-already-waiting")
            return XCTFail("an approval is already waiting before the test's question; answer it on the PC first")
        }
        let timerApprove = app.buttons.matching(NSPredicate(format: "label BEGINSWITH 'Approve with Face ID' AND label CONTAINS[c] 'timer'"))
        let timerReject = app.buttons.matching(NSPredicate(format: "label BEGINSWITH 'Reject:' AND label CONTAINS[c] 'timer'"))
        let anyApprove = app.buttons.matching(NSPredicate(format: "label BEGINSWITH 'Approve with Face ID'"))
        let receipts = app.staticTexts.matching(NSPredicate(format: "label BEGINSWITH 'Applied' OR label BEGINSWITH 'Failed' OR label BEGINSWITH 'Refused or failed' OR label BEGINSWITH 'Not answered' OR label BEGINSWITH 'Rejected' OR label BEGINSWITH 'Expired' OR label BEGINSWITH 'The Core no longer'"))

        // The question, the waiting line, the sheet, and the one waiting item checked.
        let question = approving ? "Set a timer for one minute called phone test." : "Set a timer for one minute called reject test."
        guard ask(question, shotName: "\(tag)-reply").reached else { return stopHere() }
        guard open.waitForExistence(timeout: 25) else {
            return XCTFail("no approval waiting after the timer question (is Set a timer on Ask first on the PC?)")
        }
        shot("\(tag)-waiting-line")
        open.tap()
        guard timerApprove.firstMatch.waitForExistence(timeout: 15) else {
            shot("\(tag)-sheet")
            return XCTFail("the approvals sheet shows no waiting timer")
        }
        if approving { sleep(1); shot("\(tag)-sheet") }   // REJECT goes at once: the picture comes after it
        note("\(tag): waiting items: \(anyApprove.allElementsBoundByIndex.map(\.label).joined(separator: " | "))")
        guard anyApprove.count == 1, timerApprove.count == 1 else {
            return XCTFail("more than one item waits; nothing is answered by the test")
        }
        let raisedBy = app.staticTexts.matching(NSPredicate(format: "label BEGINSWITH 'From '")).allElementsBoundByIndex.map(\.label)
        note("\(tag): raised by: \(raisedBy.joined(separator: " | "))")
        guard raisedBy.count == 1, raisedBy[0].hasPrefix("From \(phone) ·") else {
            return XCTFail("the waiting timer was not raised by this phone's question; nothing is answered by the test")
        }

        // The answer, and its receipt (one more than before).
        let before = receipts.count
        if approving {
            timerApprove.firstMatch.tap()
            note("APPROVE pressed: waiting up to 60 s for the owner's Face ID and the Core's answer")
        } else {
            timerReject.firstMatch.tap()
        }
        let until = Date().addingTimeInterval(approving ? 60 : 20)
        while Date() < until, receipts.count <= before { usleep(500_000) }
        XCTAssertGreaterThan(receipts.count, before, "no answer within \(approving ? 60 : 20) s")
        sleep(1)
        shot("\(tag)-receipt")
        note("\(tag): receipts newest first: \(receipts.allElementsBoundByIndex.map(\.label).joined(separator: " | "))")
        app.buttons["Done"].firstMatch.tap()
        sleep(4)
        if scroll.exists { scroll.swipeUp(); usleep(500_000) }
        shot("\(tag)-ask-after")
        note("\(tag): 'Approved from' lines: \(lines(containing: "Approved from").joined(separator: " | "))")
    }

    /// Read back what the approvals left (read only, no question sent): the conversation the last APPROVE belonged
    /// to with the Core's "Approved from ..." line, the waiting list and the notices; then R4: an announcement sent
    /// through Siri ("Announce to JARVIS", the words given to Siri as text), and the notices read again. The PC says
    /// the announcement aloud ("... Test texted you: Hello from the phone").
    func test8_Round5ReadbackAndAnnounce() {
        openAfterFaceID()
        tab("Ask").tap()
        sleep(3)   // the conversation's lines are read from the Core after the relaunch
        let scroll = app.scrollViews.firstMatch
        if scroll.exists { scroll.swipeUp(); usleep(500_000) }
        shot("r1-readback-ask")
        let long = app.staticTexts.allElementsBoundByIndex.map(\.label).filter { $0.count > 20 }
        note("ask lines: \(long.suffix(6).joined(separator: " | "))")
        note("'Approved from' lines: \(lines(containing: "Approved from").joined(separator: " | "))")

        // The Overview's two panels, and the two sheets read.
        tab("Overview").tap()
        sleep(2)
        let panels = app.staticTexts.allElementsBoundByIndex.map(\.label)
        note("overview words: \(panels.filter { ["NONE WAITING", "NOTHING NEW", "UNREAD", "WAITING", "SET ON THE PC"].contains(where: $0.uppercased().contains) }.joined(separator: " | "))")
        shot("r4-overview-panels-before")
        let openApprovals = app.buttons["Open approvals"].firstMatch
        if openApprovals.waitForExistence(timeout: 5) {
            openApprovals.tap()
            sleep(3)
            shot("r1-readback-approvals-sheet")
            note("approvals sheet: \(app.staticTexts.allElementsBoundByIndex.map(\.label).filter { $0.count > 3 }.prefix(12).joined(separator: " | "))")
            app.buttons["Done"].firstMatch.tap()
            sleep(1)
        }

        // R4: the announcement through Siri. Each string is taken as if spoken: the phrase, then the answers to the
        // intent's two questions ("Who is it from?", "What does it say?").
        let siri = XCUIDevice.shared.siriService
        siri.activate(voiceRecognitionText: "Announce to JARVIS")
        sleep(5)
        shot("r4-siri-1-phrase")
        siri.activate(voiceRecognitionText: "Test")
        sleep(5)
        shot("r4-siri-2-from")
        siri.activate(voiceRecognitionText: "Hello from the phone")
        sleep(8)
        shot("r4-siri-3-result")
        app.activate()
        sleep(12)   // the status reading every 10 s brings the unread count

        tab("Overview").tap()
        sleep(2)
        let after = app.staticTexts.allElementsBoundByIndex.map(\.label)
        note("overview words after: \(after.filter { ["NOTHING NEW", "UNREAD"].contains(where: $0.uppercased().contains) }.joined(separator: " | "))")
        shot("r4-overview-panels-after")
        let openNotices = app.buttons["Open notices"].firstMatch
        if openNotices.waitForExistence(timeout: 5) {
            openNotices.tap()
            sleep(3)
            shot("r4-notices-sheet")
            note("notices sheet: \(app.staticTexts.allElementsBoundByIndex.map(\.label).filter { $0.count > 3 }.prefix(12).joined(separator: " | "))")
            app.buttons["Done"].firstMatch.tap()
        }
    }

    /// Plan check 3 against 1.0.17, three times (the fix of 2026-10-10): close the app fully, open it, Face ID,
    /// and the last conversation's lines are back on Ask. Sends nothing.
    func test9_RelaunchRestoresLines() {
        let hints = ["Tailscale on", "cannot be reached", "Hold the microphone", "held on this phone", "connection dropped"]
        for round in 1...3 {
            app.terminate()
            openAfterFaceID()
            tab("Ask").tap()
            var lines: [String] = []
            let readBy = Date().addingTimeInterval(30)
            while Date() < readBy {
                lines = app.staticTexts.allElementsBoundByIndex.map(\.label)
                    .filter { label in label.count > 40 && !hints.contains(where: { label.contains($0) }) }
                if !coreNotReached && !lines.isEmpty { break }
                sleep(1)
            }
            let scroll = app.scrollViews.firstMatch
            if scroll.exists { scroll.swipeUp(); usleep(500_000) }
            shot("relaunch-\(round)")
            note("relaunch \(round): Core reached \(!coreNotReached); lines back: \(!lines.isEmpty); \(lines.suffix(2).joined(separator: " | "))")
            XCTAssertFalse(lines.isEmpty, "relaunch \(round): the last conversation's lines did not come back within 30 s")
        }
    }

    /// Check 7, the screen half: the lock switch turns on, and after a full close and reopen the lock screen comes
    /// first with UNLOCK and STOP ALL on it. Leaves the lock ON.
    func test4_FaceIDLockScreen() {
        openOnTheScreens()
        app.buttons["Phone settings"].firstMatch.tap()
        let lock = app.switches.matching(NSPredicate(format: "label BEGINSWITH 'Lock with Face ID'")).firstMatch
        XCTAssertTrue(lock.waitForExistence(timeout: 5), "no Lock with Face ID switch in the settings sheet")
        shot("settings-sheet")
        let wasOn = (lock.value as? String) == "1"
        note("lock switch at start: \(wasOn ? "on" : "off")")
        if !wasOn {
            lock.tap()
            sleep(1)
        }
        XCTAssertEqual(lock.value as? String, "1", "the lock switch did not turn on")
        shot("lock-switch-on")
        app.buttons["Done"].firstMatch.tap()
        app.terminate()
        app.launch()
        let unlock = app.buttons.matching(NSPredicate(format: "label CONTAINS 'UNLOCK'")).firstMatch
        XCTAssertTrue(unlock.waitForExistence(timeout: 15), "the lock screen did not appear after the relaunch")
        XCTAssertTrue(stopButton.exists, "no STOP ALL on the lock screen")
        sleep(2)
        shot("lock-screen")
        note("lock screen: UNLOCK \(Int(unlock.frame.width))x\(Int(unlock.frame.height)) pt; STOP ALL present: \(stopButton.exists)")
    }
}
