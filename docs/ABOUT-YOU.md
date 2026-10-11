# The You page: what JARVIS knows about the owner's life (release 1.0.19)

**The owner's word (2026-10-10):** "lets make jarvis and me more connected personally". Asked what that should mean,
the owner chose one option: "He knows my life". It was described as:
- a "You" page: the people who matter, birthdays, likes, goals and routines;
- JARVIS uses it in every answer;
- JARVIS offers to remember things the owner mentions, asking first.

The other three options were not chosen and are not built:
- he checks in on me;
- he talks like he knows me;
- he messages me first.

This also builds item 4 of the 1.0.19 list, "memory suggestions with OK" (`docs/OPENJARVIS-COMPARISON-20261010.md`),
for the owner's life.

**Status:** built and tested. The independent review is next.

## What it does

- **The page:** a "YOU" panel at the top of the Memory section ("PERSONAL CONTEXT"), across the whole width. It holds:
  - About you: lines about the owner;
  - People: a name, who they are to the owner, a birthday if wanted;
  - Dates: what it is, its day and month, the year if known;
  - Likes, Dislikes and Goals.

  "Coming up" shows the birthdays and dates of the next 30 days. The owner adds and removes entries there
  (`static/you.js`, `GET`/`POST /api/profile`). Removing an entry is the way to undo an approved offer.
- **Every question** carries a short summary in its context (`about_owner`, at most 2,500 characters):
  - what is coming up, then the lines about the owner, then people, dates, goals, likes and dislikes, newest first;
  - what does not fit is counted, to be read with `about_you`.

  The instructions tell JARVIS to use it as someone who knows the owner would, and never to recite it
  (`about_you.GUIDANCE`).
- **`about_you`** (reads): the whole page, or the entries matching some words, with what is coming up. A paired device
  may use it.
- **`remember_about_you`** (an offer):
  - JARVIS may offer to keep one thing the owner said about themselves or the people close to them, at most one per
    answer;
  - it always waits for the owner's OK on an approval card (on the PC, or on a device the owner lets approve), and the
    approval keeps exactly what the card showed;
  - a device needs the owner's "may save memories and tasks" tick to make an offer;
  - in a question marked by the guard (`docs/GUARD.md`), the card still asks, as for every tool that always asks.
- **What is refused:**
  - passwords, keys and tokens (the guard's secret patterns), `<`, `>` and control characters, and too-long text;
  - a day that does not exist (29 February only without a year or in a leap year), a year outside 1900 to next year;
  - a date on a like, dislike, goal or line about the owner;
  - more than 300 entries.

  The same entry twice is kept once.
- **Dates:** a 29 February birthday comes round on 28 February in other years. A person's age ("turns 30") and a date's
  years ("6 years") are said when the year is known.
- **Where it lives:** the `profile` table of JARVIS's database (`about_you.Profile`), so backups and restores carry it.
  The export (`/api/export`) includes it. Each entry records the release it was saved under, as the saved facts do. The
  Activity log records "you page: added/changed/removed" with the section only, never the entry.
- **The guard** leaves both tools' results as they are (`content_guard.OWN`): the page is the owner's own record.

Plainly: everything on the page goes to the AI provider with the owner's questions (Qwen on Alibaba today), as the
saved facts always have. The panel says so.

## Tests

- `test_about_you.py`, 12 tests:
  - the entries and every refusal;
  - the dates that come round, including the turn of the year and 29 February;
  - the summary and its bound, and search;
  - the permissions;
  - through the Core with a scripted model: every question carries the summary and the guidance, an offer waits and
    the OK keeps exactly the card, a denied offer keeps nothing, an offer holding a key is refused before any card, and
    the owner's own clicks.
- `test_you_view.cjs`: the panel's grouping, words and the fields of an add.
- Seen in a browser against a test copy of the Core with synthetic data: four entries added through the panel, "Coming
  up" showing a birthday in three days, then removed again.

## Not built (the owner's other options, or later)

- Check-ins and reminders of the dates (the routine's nudges could announce them).
- The phone's own view of the page. The phone can ask about it already (`about_you`); a page of its own is for the Mac
  session.
- Editing an entry in place on the panel. The Core's `update` exists; the panel removes and adds.
