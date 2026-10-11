---
name: jarvis-codex-review-brief
description: Package one JARVIS change into a tightly scoped brief for Codex as an independent reviewer. Use only when the owner asks for a Codex review, a second opinion or an independent review of a JARVIS change. Produces one brief file with the exact commit range, intent, files touched, verification evidence, open risks and explicit out-of-scope items, and states that a reviewer recommendation does not authorize implementation.
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash(git status *), Bash(git diff *), Bash(git log *), Bash(git show *)
---

# JARVIS: brief for a Codex review

Codex reviews only when the owner asks, and never writes (`CLAUDE.md`: "independent reviewer only, on owner
request; never writes"). Codex starts with none of this session's context, so the brief is everything it
knows. A narrow brief gets a useful review; a loose one gets a tour of the whole repository and a list of
things nobody asked about.

## Before writing

1. Confirm the owner asked for this review, and for which change. One change per brief.
2. The change must be committed, so that the brief can name it exactly. Get the range and the file list:
   `git log --oneline <base>..<head>` and `git diff --stat <base>..<head>`.
3. Have verification evidence from this session (the `jarvis-verify` report). If there is none, say so in
   the brief; do not write one from memory.
4. Keep secrets out: nothing from `.env`, tokens, keys, or the owner's personal data or memory.

## The brief

Write it to `docs/codex-reviews/<yyyymmdd>-<short-name>-brief.md`. Aim for two pages. Do not paste the diff;
give the range and let the reviewer read the code.

```
# Review brief: <short title>
Date: <yyyy-mm-dd>   Repository: C:\Users\jonny\JARVIS-claude-workspace\repo   Branch: claude/main
Range under review: <base sha>..<head sha>   (git diff <base>..<head>)
Writer: Claude Code (sole writer).   Reviewer: Codex (independent, read-only).

## Your role and its limits
You are reviewing, not writing. Read the range above and report findings. Do not edit, commit, build,
install, run anything that changes state, or contact any remote. A reviewer recommendation does not
authorize implementation: your findings go to the owner, the owner decides, and Claude Code is the only
writer.

## Intent
<What the change is for and why, in 2-5 sentences. What should behave differently now. What must not
have changed.>

## Files touched
<path>: <one line on its role in the change>   (every file in the range; mark tests as tests)

## Verification evidence
<The jarvis-verify table: check, command, result, the pasted result lines.>
Not verified: <everything that was skipped or could not be run here, stated plainly>

## Open risks and known limits
<What the writer is least sure of. Known limitations. Anything deliberately left for later.>

## Questions for the reviewer
1. <3 to 6 specific questions, each answerable from the range>

## Out of scope
- Anything outside the range above, including older code these files call, unless it makes this change wrong.
- Stage 6 gates, checkpoints, evidence and the acceptance VM; FINAL selection; cutover; Stage 7.
- The live JARVIS installation and the original source at C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis.
- Networking, remote access and how the Core is reached (bound to 127.0.0.1 by owner decision).
- <anything else specific to this change>

## How to answer
One entry per finding: severity (blocks / should fix / note), file and line, the concrete input or state
that goes wrong and what happens, and a suggested direction in words. No patches. If you find nothing, say
what you checked.
```

## Rules for filling it in

- **Intent is the writer's claim, not the reviewer's conclusion.** State it so that the reviewer can find
  where the code falls short of it.
- **Evidence is quoted, not summarized.** "Tests pass" is not evidence; the result lines are. Skipped and
  failed steps appear as SKIPPED and FAILED.
- **Risks are honest.** The point of an independent review is to look where the writer is unsure; hiding
  the weak spot wastes the review.
- **Out of scope is explicit.** Anything not listed as in scope will be reviewed anyway unless the brief
  says otherwise.

## Handing it over, and afterwards

Tell the owner where the brief is; the owner gives it to Codex. Do not send it anywhere yourself.

When findings come back, record them next to the brief (`...-findings.md`), give the owner a plain-language
view of each one (agree, disagree, unsure, and why), and wait. A finding is advice. Changing code because of
it is a new piece of work that the owner approves like any other.
