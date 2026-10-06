# Music by nickname (release 1.0.16, item 5): DRAFT

Status: **DRAFT, not built (2026-10-06, Claude Code).** On the owner's words "music from files, add to 1.0.16" and
"so draft this up but then get back to the phone": the design is written here; the building follows once the
phone release's items 1 to 4 are reviewed and committed. Nothing of this is in the code yet.

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

- **The player (`music.py`).** The Core plays the file itself through Windows' own media interface (winmm, the same
  system part that has played sound files since Windows 95; no extra package). So the music plays whether the
  JARVIS window is open, minimised or in the tray, and pause, resume, stop and volume are immediate. One song at a
  time; a new "play" replaces the one playing. The player says plainly when a file is missing, cannot be played or
  there is no sound device (the test VM has none).
- **The list (`Store`, table `music`).** Nickname -> file name. Kept in the database, so it is in every backup;
  the music files themselves are not backed up (they are yours, and large): a restore into another installation
  shows a nickname whose file is missing, and you copy the file again.
- **The commands.** Answered by the Core before anything else, like the memory commands: "play <name>" (a nickname
  first, else a file name that contains the words), "stop the music" / "stop playing", "pause the music" / "pause",
  "resume" / "continue the music", "volume up" / "volume down" / "music volume <0-100>", "what is playing". "Play a
  video ..." and "spotify play ..." stay what they are (YouTube and Spotify). A "play" that matches no song goes to
  the AI as an ordinary question, so "play something by AC/DC" can still be answered by the model, which gets the
  list through the tool below.
- **One tool row, `play_music`** (Settings > Permissions: "Play music from your files", a change on this PC, undo
  "say stop the music", switch positions Allowed / Ask first / Off), with actions play, pause, resume, stop, volume,
  status and list. The AI model may call it for your phrasing the Core did not recognise; your own buttons in
  Settings > Music call it too. Not for paired devices (it is the PC's speakers).
- **The emergency stop stops the music** at once, with everything else; RESUME does not restart it.
- **Settings > Music** (`static/music.js`, `music.css`): the folder's path with REFRESH and the files found; the
  nickname list with ADD and REMOVE; PLAY on each row; a "Now playing" line with PAUSE, RESUME and STOP; a volume
  slider (setting `music_volume`, 0 to 100, kept in Settings as the others are). The dashboard shows the song that
  is playing in its activity line.
- **The spoken reply:** "Playing Shoot to Thrill." (the file name without its ending); "Nothing is playing."; "No
  song called workshop warrior. Your songs: ...".

## Not in this item

Reading tags inside the files (the file name is the title); playlists and "next"; playing on the phone or any
other device (version 2 of the phone, where the phone's own speakers would play); Spotify (what exists stays as
it is); fading between songs; a start-up song (a separate decision, the file version is now possible on top of
this).

## Checked (to do when built)

`test_music.py`: the player's commands with the system part replaced by a recorder (no sound in the tests); the
nickname list and the matching of spoken names; every command phrase; the tool row and its switch; the stop; the
routes; a missing file and a file that cannot be played said plainly. `test_music_view.cjs`: the words of the
panel. `test_permissions.py` holds the table equal to the tools, so the new row is counted there. A real song on
this PC's speakers once, by the author, in a sandbox Core.
