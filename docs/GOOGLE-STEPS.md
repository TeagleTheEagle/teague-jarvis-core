# Gmail and Google Calendar for JARVIS: your steps (item G of docs/PHONE-ACCESS-PLAN.md)

Two things only you can do, once. Both put a line in your key file; Claude never sees the values. Nothing
here needs a Google Cloud project or a sign-in screen, and nothing expires every week (a Google "OAuth app" in
testing status would: its sign-in dies after seven days, so JARVIS does not use one).

## 1. Gmail: JARVIS's own account, with an app password (read, search and send mail)

**Your decision (2026-10-10): "his own account only".** JARVIS gets a Google account of his own and your account stays
out of his reach. He sends from his own address and reads only his own inbox: forward him a mail when he should see
it. JARVIS holds one Gmail account, so your own inbox is not connected.

JARVIS reads his mail over IMAP and sends over SMTP, the way a mail program does, with an **app password**: a
sixteen-letter password Google makes for one program. It needs 2-Step Verification on JARVIS's Google account.

0. Make JARVIS's account (yours to do; Claude never makes accounts): on a browser, **accounts.google.com/signup**, a
   personal account, with your own phone number for Google's check. Keep its password in your own records; never
   give it to JARVIS or to Claude. Stay signed in to this new account for steps 1 to 4.
1. On any browser, signed in to **JARVIS's** Google account: **myaccount.google.com** > **Security**.
2. Under "How you sign in to Google", make sure **2-Step Verification** is **On** (turn it on if not; Google walks
   you through it with your phone).
3. Open **myaccount.google.com/apppasswords** (or search "App passwords" in the Security page). If Google asks for
   your password, give it there, never to JARVIS or to me.
4. App name: `JARVIS`. Click **Create**. Google shows sixteen letters in four groups. Copy them (spaces do not
   matter).
5. On the PC, Win+R, then:

   ```
   notepad %LOCALAPPDATA%\JARVIS\config\.env
   ```

   (That is the key file that already holds your AI keys, in the `config` folder. A development copy of JARVIS
   reads `.env` beside `server.py` instead.) Add two lines (JARVIS's new address, and the sixteen letters):

   ```
   GMAIL_ADDRESS=jarvis-address@gmail.com
   GMAIL_APP_PASSWORD=abcd efgh ijkl mnop
   ```

   Save. Quit JARVIS completely (its icon near the clock) and start it again.
6. In JARVIS: Settings > Connections shows **Gmail: Configured** and a **TEST** button that signs in once and says
   how many unread mails you have. Nothing else is read until you ask, except this: once your phone shows its
   Overview, JARVIS reads the unread count every five minutes in the background for that screen.

What JARVIS can then do with his inbox: "any new mail?", "search the mail for the invoice from Jack", "read the
mail from Mum" (once you have forwarded it to him), "send Jack a mail saying you're running late" (it leaves from
JARVIS's address). **Sending always asks you first** (on the PC's screen, or on the phone once the approve tick is
on): you see to whom, the subject and the text before anything leaves.

Plainly: whatever JARVIS reads from his mail goes to the AI provider with your question (Qwen on Alibaba today),
as every question does. You can revoke the app password at any time at myaccount.google.com/apppasswords (signed
in as JARVIS); JARVIS then says "Gmail refused the app password" and reads nothing. Your own Gmail can forward
every mail to him automatically (your Gmail's Settings > Forwarding); then all your mail reaches JARVIS and the AI
provider, so that is your choice, and not needed.

## 2. Google Calendar: the calendar's private address (read your events)

Each Google calendar has a secret address that gives its events to a program that knows it, without a sign-in.

1. On a computer browser: **calendar.google.com** > the gear > **Settings**.
2. On the left, under "Settings for my calendars", click the calendar JARVIS should read. **Each calendar has its own
   secret address**, and JARVIS reads only the calendars whose addresses are in the key file: an event on another
   calendar (the name beside it in Google Calendar) does not reach him.
3. Scroll to **Integrate calendar**. Copy the **Secret address in iCal format** (it starts with
   `https://calendar.google.com/calendar/ical/` and ends with `/basic.ics`). Do not use the public address.
4. In the key file (step 5 above), add one line. For more than one calendar, separate the addresses with commas:

   ```
   GOOGLE_CALENDAR_ICS=https://calendar.google.com/calendar/ical/.../private-.../basic.ics
   ```

   Save, quit JARVIS completely, start it again.
5. Settings > Connections shows **Google Calendar: Configured** and a **TEST** button that fetches the calendar once
   and says how many events are in the next seven days. Once your phone shows its Overview, the next day's events are
   read every ten minutes in the background for that screen.

What JARVIS can then do: "what's on today?", "when is my next appointment?", "am I free Thursday evening?", the
daily briefing's calendar part, and the phone's Upcoming panel. Reading only: adding an event needs a Google
sign-in screen (the weekly-expiring kind), which is a separate decision ("calendar add"). If you ever reset the
secret address in Google's settings, put the new one in the key file.

## 3. If something is off

- "Gmail: not configured": one of the two lines is missing or misspelled; the key file is read at JARVIS's start.
- TEST says the password was refused: 2-Step Verification is off, or the app password was deleted; make a new one.
- TEST says the calendar address was refused: it was reset in Google's settings, or the public address was used.
- JARVIS says a day is empty but Google Calendar shows an event: the event is on a calendar whose secret address is
  not in the key file (2026-10-10: "will's party" reached JARVIS once you put the calendar's address in again). Add
  that calendar's address after a comma, quit JARVIS completely and start it again. A new event can also take up to
  ten minutes to reach JARVIS, because he keeps what he read for ten minutes.
- JARVIS never writes to his mailbox except to send what you approved (Gmail itself keeps a copy of each sent mail
  in Sent, as it does for any mail program); in 1.0.17 he does not mark mail read, delete or move anything.
