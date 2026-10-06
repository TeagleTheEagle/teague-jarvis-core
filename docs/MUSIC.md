# Music by nickname (release 1.0.16, item 5)

Status: **BUILT in the repo on 2026-10-06 (Claude Code), after items 1 to 4 of the phone release were reviewed and
committed (007a5ab).** On the owner's words "music from files, add to 1.0.16" and "so draft this up but then get
back to the phone": this record was first the design (a draft), then the record of what was built. Independent
review: section at the end. Not in any release yet.

## In plain words

You say "Jarvis, play workshop warrior" and Shoot to Thrill plays on the PC's speakers. The songs are your own
music files, copied by you into a folder JARVIS keeps; a nickname points at each file. "Stop the music",
"pause", "resume", "volume up" and "volume down" work the same way. No AI is involved in these commands: the Core
answers them itself, so they start at once and work offline.

## Your part

1. Copy the music files you own into the folder JARVIS shows you in Settings > Music (inside JARVIS's config
   folder, which every update keeps). MP3 is the safe choice; WAV works too. I cannot fetch any song for you.
2. In Settings > Music, give each song a nickname (the first one: workshop warrior = Shoot to Thrill). A song
   without a nickname can still be played by its file name ("Jarvis, play shoot to thrill").

## What is built

- **The player (`music.Player`).** The Core plays the file itself through Windows' own media interface (winmm's
  `mciSendString`, the part of Windows that has played sound files since Windows 95; no extra package): `open ...
  type mpegvideo`, `play`, `pause`, `resume`, `stop`, `setaudio volume`, `status mode/position/length`, `close`. So
  the music plays whether the JARVIS window is open, minimised or in the tray, and pause, resume, stop and volume
  are immediate. One song at a time; a new "play" replaces the one playing; a song that has ended is noticed at the
  next look and closed (a passing state such as "seeking" right after play counts as playing). The file's path is
  handed over in its short (8.3) form when the drive keeps one, otherwise as it is, quoted (that is how the sandbox
  check on D: played); a path over 260 characters on a drive without short names fails with Windows' own words. No
  song starts while the emergency stop holds, also when the stop lands in the moment a song is being opened. The
  player says plainly when a file cannot be opened (Windows' own words, one sentence) or when nothing is playing;
  off Windows, or without a sound device (the test VM), "play" fails with a plain message.
- **The list (`music.Library`, table `music` in the database).** Nickname -> file name; a nickname is one name
  whatever its case ("Workshop Warrior" and "workshop warrior" are the same row). In every backup with the database;
  the music files themselves are not backed up (they are yours, and large): a restore into another installation
  shows a nickname whose file is missing ("file not in the folder"), and you copy the file again. The folder:
  `<config folder>\music` in an installation (`%LOCALAPPDATA%\JARVIS\config\music`, kept across updates); beside the
  data of an isolated instance; made by JARVIS when it starts, so the path the panel shows exists. MP3 and WAV are
  listed; sub-folders and hidden files are not. (In a development copy the folder is `<repo>\music`, ignored by git.)
- **The commands** (`music.command`, answered by the Core itself like the memory commands, before any AI): "play
  <name>" (compared word by word: a nickname first, the same words or, for a nickname of two words or more, all its
  words said, or, for four letters or more, the words said all in the nickname; then a file whose name holds every
  word said; "the", "a", "my" in front are ignored; filler words alone, "play it", "play the", name nothing),
  "stop the music" / "stop playing" / "music off", "pause" / "pause the music", "resume" / "continue the music" /
  "unpause", "volume up" / "volume down" / "louder" / "quieter" / "volume 40" / "set the volume to 65 percent",
  "what's playing" / "what song is this". With or without "Jarvis," and "please". **The bare words ("pause",
  "resume", "continue", "volume up", "louder", "volume 40") are music only while a song is open;** with nothing
  playing, "continue" asks for the rest of an answer and "louder" may be about JARVIS's voice, so they go to the AI
  as before. The forms that name the music ("pause the music", "music volume up", "set the volume to 40") always
  are. "Play a video ...", "... on YouTube", "spotify play ..." and "... on Spotify" are never music. **A "play"
  that matches no song is not a music command:** the words go to the AI as an ordinary question, so "play something
  by AC/DC" can still be answered by the model, which gets the list through the tool below. Never for a paired
  device (the PC's speakers).
- **One tool row, `play_music`** (Settings > Permissions: "Play music from your files", a change on this PC, undo
  "say stop the music", switch positions Allowed / Ask first / Off; `status` and `list` are reads), with actions
  play, pause, resume, stop, volume (0 to 100), status and list. The spoken commands run through it, so your switch
  applies to them: Off refuses the command with its usual sentence, Ask first asks on the PC. The AI model may call
  it for a phrasing the Core did not recognise; your own buttons in Settings > Music call it too (a click is its own
  approval, as every button in the interface). Not for paired devices.
- **The emergency stop stops the music** at once, with everything else; RESUME does not restart it.
- **Settings > Music** (`static/music.js`, `music.css`; the category is new in `static/teague.js`): the folder's
  path with REFRESH; "Now playing" with PAUSE / RESUME / STOP and the position; the volume slider (setting
  `music_volume`, 0 to 100, kept in Settings and used for the next song too; "volume up" by voice moves it by 10);
  "Give a song a nickname" (nickname, file, ADD; a song without a nickname can still be played by its file name);
  the nickname list with PLAY and REMOVE, and "file not in the folder" when a file is gone.
- **The spoken reply:** "Playing Shoot to Thrill." (the file name without its ending); "Paused Shoot to Thrill.";
  "Resuming ..."; "Stopped ..."; "Music volume 90 percent."; "Playing Shoot to Thrill (your nickname workshop
  warrior)." for "what's playing"; "Nothing is playing."; "No song called highway to hell. Your songs: workshop
  warrior, Back in Black, Thunderstruck." (nicknames first, then the songs without one, twelve at most).
- Owner routes: `GET /api/music` (folder, files, nicknames, now, volume), `POST /api/music` (add, remove, play,
  pause, resume, stop, volume, status). Activity rows: `play_music` for every call as for every tool, "music nickname
  added/removed".
- **Not done from the draft:** the dashboard does not yet show the song in its activity line (Settings > Music
  does); it can follow.

## Not in this item

Reading tags inside the files (the file name is the title); playlists and "next"; playing on the phone or any
other device (version 2 of the phone, where the phone's own speakers would play); Spotify (what exists stays as
it is); fading between songs; a start-up song (a separate decision, the file version is now possible on top of
this).

## Checked

- `test_music.py` (9 tests): the list (files, nicknames, a nickname's file gone, bad input, a missing folder); the
  matching of spoken names (exact, contained, with "the", file-name words, a nickname whose file is gone resolves
  to nothing); the player with the media interface replaced by a recorder (every command sent, pause/resume/stop/
  volume, a song that ended, a file that cannot open, a replacement); the command phrases (what is music and what
  is not); the desk's actions and spoken replies; and through a real local Core: the routes, the spoken commands
  answered without any AI key, the volume kept in Settings, a "play" that matches nothing going on as an ordinary
  question, the panel's buttons, the activity rows; the owner's switch (Off refuses the spoken command, the owner's
  button still works; Ask first asks on the PC), the AI model calling the tool, the emergency stop stopping the
  music and RESUME not restarting it, no music for a paired device; the permission row.
- `test_music_view.cjs`: the words of the panel. `test_permissions.py` holds the table equal to the tools and the
  receipt list (the row is in both); `test_inspection_browser.py` holds the static list equal to what the window
  loads (`music.js`, `music.css` added). The owner-run request template (`tools/host/jarvis-request-*`) regenerated
  with the 46th tool.
- **A real sound on this PC once** (2026-10-06, by the author, from a plain Python process with the real media
  interface, volume 25): a generated two-second tone played, position 768 ms after 0.8 s, pause and resume
  worked, and after the song ended the player read "nothing" and closed it. No music file of the owner's was used.
- Whole development tree after the item and its review fixes: 663 Python tests, 52 desktop tests, 18 Intelligence
  tests and 24 interface scripts pass.

- **In a window** (sandbox preview Core, synthetic data, both provider keys blank, port 8799; Edge through
  Playwright at 1280 x 900; pictures and the words read from the page in
  `docs/release-rehearsal-20261006-1016/music-panel/`): Settings > Music shows the folder
  (`D:\JARVIS-release-work\dashboard-preview\config\music`), "1 music file", "Nothing is playing.", and no Save bar;
  the volume slider set to 20 and saved; a nickname "workshop warrior" given to the tone stand-in file; PLAY: "Playing:
  Shoot to Thrill (tone stand-in) (workshop warrior) 0:00 / 0:02" with PAUSE and STOP, and the tone was heard on this
  PC; PAUSE: "Paused: ... 0:01 / 0:02"; STOP: "Nothing is playing."; REMOVE took the nickname off. The owner's real
  installation was not touched.

Not checked: an MP3 file (the tone was WAV; the `mpegvideo` device plays both, but no MP3 was on hand), the desktop
app itself, the test VM (no sound device: "play" says so), a spoken command through the real microphone.

## Independent review (one reviewer, 2026-10-06): no high finding; 2 medium and 10 low, all applied

The reviewer read the record, the module and the Core's changes in full, ran the music, permission, static-list and
answer-mode test modules and its own experiments with an isolated Core and the media interface replaced (no sound,
nothing of the installed JARVIS touched). The fixes were not reviewed again; the tests of "Checked" cover them.

**Medium**

1. The bare words "pause", "resume", "continue" and "what is this" were music commands even with nothing playing,
   so a plain "continue" (the ordinary way to ask for the rest of an answer) failed with "Nothing is paused." (run).
   **Fixed:** the bare words are music only while a song is open; "what is this" is no music command at all; the
   forms that name the music always are (section "The commands").
2. Names were matched by letters inside words: a nickname "ice" played for "play nice music", "play a" played a
   song whose nickname contained the letter, and "play it" / "play the" picked a file by a filler word (run).
   **Fixed:** words, not letters; filler words alone name nothing; a one-word nickname is found only when said as
   the whole name.

**Low**

3. A passing player state right after "play" ("seeking") closed the song that had just opened, and the reply then
   crashed on a missing title (run with a stand-in). **Fixed:** only "stopped" closes; the replies are built from
   the song that was acted on, not from a status read afterwards.
4. "Volume up", "louder" and "turn it up" always went to the file player, also with nothing playing and also when
   Spotify was what played (run). **Fixed** with finding 1: bare volume words only while a song is open.
5. The music folder was never created, so the panel showed a path that did not exist (run). **Fixed:** made when
   the list is set up.
6. A list where a nickname should be, sent to "remove", was a 500 and an "internal error" row; a name with spaces
   around it was not found (run). **Fixed:** checked and stripped.
7. Nicknames were case-sensitive keys: "Workshop Warrior" and "workshop warrior" were two rows (run). **Fixed:**
   one name whatever its case (a table made earlier by a development copy is rebuilt once).
8. A "play" that had passed the permission gate in the moment before an emergency stop played after the stop and
   kept playing (run with a forced ordering). **Fixed:** the player asks whether the stop holds right before a
   song opens and again right after.
9. A volume saved through `/api/settings` did not reach the player until the next slider move (run). **Fixed:**
   the player takes the saved volume before every tool call and listing.
10. The "No song called ..." reply repeated the whole query, up to 12,000 characters from the model (run).
    **Fixed:** cut to 60.
11. The panel rebuilt the volume slider and the file choice under the owner's hand every three seconds, and a
    slider move during another request was dropped (read). **Fixed:** nothing in the "Now playing" or the "Give a
    song a nickname" box is redrawn while the cursor is in it; a slider move during a request is sent afterwards.
12. Records: `docs/PERMISSIONS.md` said 45 tools (46 now); this record's sentences on the bare words, the
    matching, the short path and the nickname characters said more or less than the code. **Fixed** in each.
13. Note: the new files had to be in the commit for a release build (they are), and a development copy's music
    folder would have made the tree dirty: `/music/` is now ignored by git.

**Checked by the reviewer and found correct:** every music call passes the one permission gate (the spoken
command, the model's call, the owner's buttons, an approval); Off refuses JARVIS's calls and leaves the owner's
button working; Ask first keeps the exact call; while stopped, play, pause and status are refused with the stopped
sentence and the list can still be edited; the routes need the owner's session and a paired device can reach none
of it; the model is held to an integer volume; the emergency stop words and the window's own "stop" are not music;
"play a video" and "spotify play" keep their tools; no path traversal (only a listed file name is accepted), only
MP3 and WAV, no sub-folders; the music folder is not in a backup and the table travels with the database;
`music_volume` is an integer 0 to 100 and cannot come in through an import; line endings kept; the static list, the
settings category, the save bar and the request template are right; the player's locks; RESUME does not restart
the music.

**Not reached by the review:** the real media interface (the state right after play, `resume` on the mpegvideo
device, a drive without short names, a path over 260 characters, a slow drive, MP3 files); the panel in a browser;
the desktop app; the test VM; a spoken command through a microphone; the carrying out of an approved "play".
