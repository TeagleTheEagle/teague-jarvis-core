# The guard on what JARVIS reads (release 1.0.19, item 1)

**The owner's word:** "build all of these" (2026-10-10). The eight items are in `docs/OPENJARVIS-COMPARISON-20261010.md`,
and the guard comes first, because mail, skills, web pages and messaging all depend on it.

**Status:** built and tested. Tests of the touched modules pass, 190 tests. **The independent review has not run
yet:** that is the next session's first step, then the findings, the full suite and the record of the review here.

## What it does

`content_guard.py`. Every tool result passes `content_guard.guard()` at the end of `server.App.tool`, before the AI
model reads it, whoever asked: the model, a local command or an approval being carried out.
- **Invisible text:**
  - silently removed: zero-width spaces, direction marks, the soft hyphen and the byte-order mark;
  - removed and reported: direction overrides and isolates, and the tag characters that carry text nobody can see;
  - kept: the joiners U+200C and U+200D, which emoji and some scripts need.
- **Instructions to an AI:** the whole sentence around a match is replaced by a marker. Six kinds are caught:
  - "ignore your/previous/system instructions";
  - a new identity ("you are now DAN", "from now on you will ignore ...");
  - a fake conversation turn (`<|im_start|>`, `[INST]`, "## System");
  - words addressed to an AI ("note to AI assistants", "if you are an AI");
  - "do not tell the user";
  - requests to send private data or reveal the instructions.

  The patterns are narrow on purpose, so "ignore the instructions on the packet", "send the invoice to accounts@...",
  "You are now subscribed" and "System: Windows 11" pass. They are bounded: about 4.5 MB of deliberately nasty text
  takes about a second.
- **Secrets** are blacked out: API keys (OpenAI and DashScope `sk-`, Groq, Google, GitHub, Slack, AWS, Telegram),
  signed tokens, bearer tokens, private-key blocks, `..._API_KEY=` / `..._PASSWORD=` values to the end of their line
  (a Gmail app password has spaces), and passwords inside web addresses.
- A changed result carries a `guard` note for the model, and the Activity log gets a row "guard: <tool>".
- **The question is marked** when instructions or hidden text were found (`run.tainted`). From then on in that
  question, every tool that changes something waits for the owner's approval, whatever its switch, or is refused
  when it cannot wait (`permissions.decide(tainted=...)`, `permissions.TAINTED_MESSAGE`). Reading goes on, and the
  owner's own clicks are never affected.
- **Earlier research and evidence** in a question's context also pass the guard, because research was saved as it
  came.
- **The page opener** (`computer_open_page`) opens an address on this PC, the home network or the private network
  only when the owner's own words in the question name it (`content_guard.local_address`, `owner_named`). That
  covers loopback, private, link-local and 100.64/10 (Tailscale) addresses, and names without a dot or under .local,
  .lan, .home, .internal and .ts.net. The chat window renders no images from links, so there is no image-link
  channel to leak through.

The idea follows OpenJarvis's `security/injection_scanner.py` (Stanford, Apache-2.0). The patterns are written anew
and nothing is copied.

## Tests

`test_content_guard.py` has 12 tests:
- every attack is caught, and every ordinary text passes;
- hidden text is handled;
- secrets are blacked out;
- a result keeps its shape and carries the note;
- no text makes it slow;
- local addresses are recognised;
- the tainted decision;
- through the Core: a poisoned search result is cleaned and logged and marks the question, after which a timer
  waits for approval; a clean result changes nothing; the page opener's rule holds.

## Known limits

- Patterns catch the common ways of instructing a model, not every possible wording. The note, the marking and the
  approval of changes are the safety net.
- Pictures are not read for hidden instructions.
- A Workshop command's own network access is not limited by this guard; its output is.
