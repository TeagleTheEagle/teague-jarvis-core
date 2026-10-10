# The guard on what JARVIS reads (release 1.0.19, item 1)

**The owner's word:** "build all of these" (2026-10-10). The eight items are in `docs/OPENJARVIS-COMPARISON-20261010.md`,
and the guard comes first, because mail, skills, web pages and messaging all depend on it.

**Status:** built, tested and independently reviewed. The review found 4 high, 5 medium, 1 low-medium and 4 low findings. All are
applied (section "Review" below). `test_content_guard.py` has 18 tests.

## What it does

`content_guard.py` works on **what the AI model reads, and only that**:
- every tool result, in the Core's tool loop (`server.py`) and in the Workshop's mission loop (`workshop.py`), through
  `for_model`;
- the research and tool results of earlier questions that a question's context gives the model again (`earlier`);
- an attached file;
- the Workshop's lessons and latest mission in a question's context;
- the file names and lessons in a mission's opening instructions.

The window, the owner's own clicks and local commands get every result exactly as the tool gave it. So an approval card
always shows exactly what will run.

What the guard does to that text:
- **Invisible text:**
  - silently removed: zero-width spaces, direction marks, the soft hyphen, word joiners, the byte-order mark, and the
    direction embeddings and isolates (common around names and phone numbers on web pages);
  - removed, reported and marking the question: the direction overrides U+202D and U+202E, and stray tag characters
    (text nobody can see);
  - kept: emoji flags such as Scotland's, which use tag characters, and the joiners U+200C and U+200D, which emoji and
    many scripts need. Those joiners are removed only between two Latin letters ("Ig<U+200D>nore").
- **Instructions to an AI:** the whole sentence around a match is replaced by a marker. A line that is cut keeps its
  line break. Six kinds are caught:
  - "ignore your/all previous instructions";
  - a new identity ("you are now DAN", "from now on you will ignore ...");
  - a fake conversation turn (`<|im_start|>`, `[INST]`, a line "## System:", also in a numbered file read);
  - words addressed to an AI ("note to AI assistants", "if you are an AI"; "AI" and "LLM" count in capitals only);
  - "do not tell the user about this";
  - requests to send the owner's private data or to reveal the system prompt.

  The patterns are narrow on purpose. For example, all of these pass:
  - "ignore the instructions on the packet";
  - "please disregard the previous instructions; the meeting is at 3pm";
  - "enable Developer Mode";
  - "Hey Jarvis";
  - "Dear Assistant";
  - "never show the user a negative number";
  - "send the password for the wifi?".

  A text with more than 100 matches is cut out whole.
- **Secrets** are blacked out:
  - API keys (OpenAI, Anthropic, Fish Audio and DashScope `sk-`, Groq, Google, GitHub, Slack, AWS, Telegram), signed
    tokens, bearer tokens and private-key blocks;
  - a setting as a key file writes it: a name in capitals ending in API_KEY, SECRET, TOKEN or PASSWORD at the start of
    a line, to the end of that line (a Gmail app password has spaces);
  - passwords inside web addresses.

  Code such as `new_password == confirm` or `apiToken = getToken()` stays as it is.
- **Changes and the note:** a changed result carries a `guard` note for the model, and the Activity log gets a row
  "guard: <tool>".
- **The question is marked** when instructions or hidden text were found (`run.tainted`). From then on in that question:
  - every tool that changes something waits for the owner's approval, whatever its switch (`permissions.decide(tainted=...)`);
  - a tool that always asks keeps its own approval card, which shows exactly that call (sending a mail, a change to
    JARVIS's own files, a drafted action);
  - a tool that needs the owner's own words keeps that check, which outside text cannot meet (timers, saved facts, the
    window's controls);
  - a change inside the window, which cannot wait for an approval, is refused, with what to do instead
    (`permissions.TAINTED_MESSAGE`);
  - reading goes on, and the owner's own clicks are never affected.
- **The mark carries on:** text the guard already cut counts again when it comes back in a later question's context, so
  that question is marked too while the text is in front of the model. A new conversation starts clean.
- **Left as they are:**
  - JARVIS's own records and program files (`content_guard.OWN`): the owner's notes, facts, tasks, projects and chats,
    JARVIS's own source and history, timers and drafts. Secrets in them are not blacked out either: the owner's note
    may hold a password the owner asks for.
  - The AI model's own arguments shown back for approval (`MODEL_OWN_KEYS`).
- **Writing back the guard's stand-ins is refused.** A Workshop write or append, or a proposed change to JARVIS's own
  files, that holds "[secret removed]" or the marker, where the file does not already hold it, would replace real
  content with the stand-in (`content_guard.placeholders`, `WRITE_BACK`).
- **The page opener** (`computer_open_page`) opens an address on this PC, the home network or the private network at
  once only when the owner's own words name it as a whole; otherwise the owner is asked, and the approval opens it.
  - Local addresses: loopback, private, link-local, reserved and 100.64/10 (Tailscale) addresses, in every form a browser
    accepts (127.1, 0x7f.0.0.1, 2130706433, a trailing dot, a backslash, percent escapes, IPv4 inside IPv6); names without a
    dot or under .local, .lan, .home, .internal, .localhost, .ts.net and .home.arpa; and names whose address is such an
    address (looked up, at most 2 seconds).
  - A one-word name ("printer") is named only when written as an address ("http://printer", "printer:631").
  - The chat window renders no images from links, so there is no image-link channel to leak through.
- **Approval cards** show the characters that hide or reorder text as their codes (`⟨U+202E⟩`), so what the owner reads
  on the card is what runs (`static/reliability.js`).

The idea follows OpenJarvis's `security/injection_scanner.py` (Stanford, Apache-2.0). The patterns are written anew
and nothing is copied.

## Tests

`test_content_guard.py`, 18 tests:
- every attack is caught, and every ordinary text, mail and piece of code passes;
- hidden text is handled, and emoji flags stay whole;
- secrets are blacked out;
- a result keeps its shape, keys are cleaned, too-deep parts are left out, the model's own arguments stay, and a text
  read again keeps its mark;
- the inputs that were slow are fast (the whole test well under 10 s);
- local addresses in every form;
- the owner naming one;
- the tainted decision, also for tools that always ask or need the owner's own words.

Through the Core with a scripted model:
- the approval card is exactly what runs;
- writing the stand-ins back is refused;
- a local page opens on the owner's words or approval;
- a poisoned search result is cleaned for the model only, logged, marks the question, and the mark carries to the next
  question but not to a new conversation;
- an attached file passes the guard;
- JARVIS's own records reach the model as they are;
- a mission's reads pass the guard and mark it.

## Known limits

- Patterns catch the common ways of instructing a model, not every possible wording. Another language, synonyms, or
  full-width or look-alike letters can evade them. The note, the marking and the approval of changes are the safety
  net.
- Text that quotes an attack (an article about prompt injection) is cut and marks the question. Text the owner wrote
  into JARVIS's own records is never scanned.
- Pictures are not read for hidden instructions.
- A Workshop command's own network access is not limited by this guard, only its output. A command can still write
  any file.
- A name whose address changes between the page opener's check and the browser's own lookup (DNS rebinding) is not
  covered.

## Review (2026-10-10, one independent reviewer agent, on commit 0c819b6)

| # | Severity | Finding | What was done |
|---|---|---|---|
| 1 | high | The approval card showed the guarded copy; approving ran the original. | The guard runs only where the model reads results (`for_model`), not inside `App.tool`. The model's own arguments are never changed. The card shows hiding characters as codes. |
| 2 | high | The model could write back text the guard had changed (`[secret removed]`, the marker), corrupting files. | Writes that carry the guard's stand-ins are refused unless the file already holds them. The setting pattern is capitals-only and line-start. A cut line keeps its line break. |
| 3 | high | The mark did not carry to the next question, although the same text was still in its context. | `earlier()` marks the question, and the marker itself counts when read again. |
| 4 | high | An attached file's text never passed the guard. | It does, and it marks the question. |
| 5 | medium | Frequent false alarms (mail corrections, "Developer Mode", "Hey Jarvis", code comments, flags, isolates). | Patterns narrowed; isolates and embeddings removed quietly; flags kept; JARVIS's own records exempt (`OWN`). |
| 6 | medium | Local addresses in other notations (127.1, trailing dot, backslash) bypassed the page opener's rule; `owner_named` matched substrings. | Browser-style host reading, WHATWG IPv4 forms, a name lookup, and whole-word naming. |
| 7 | medium | The owner's approval to open a local page was then refused. | The rule asks first, and the approval opens. |
| 8 | medium | In a marked question, tools that always ask were refused, with a wrong message. | They keep their own approval; own-words tools keep their check; the message is corrected. |
| 9 | medium | Three patterns were quadratic; the speed claim was untrue. | Lookbehinds, possessive quantifiers and a cap of 100 matches; the slow inputs are in the test. |
| 10 | low-medium | The owner's own data and clicks were rewritten. | No guard outside the model's reading. |
| 11 | low | The fake-turn pattern missed numbered file reads and Windows line ends. | Both are allowed. |
| 12 | low | Deep values and dict keys passed unguarded. | Keys are cleaned; too-deep parts are replaced by a placeholder. |
| 13 | low | Other routes into the model: mission file names and lessons, errors, the Workshop's context. | All pass the guard. |
| 14 | low | A joiner inside a word evaded the patterns; doc gaps. | Joiners between Latin letters are removed; this record is rewritten. NFKC normalisation is not done (known limits). |

The reviewer's check scripts were rerun on the fixed code, and each finding's scenario now behaves as the table says.
