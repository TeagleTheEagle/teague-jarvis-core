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
