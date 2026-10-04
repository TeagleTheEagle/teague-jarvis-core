# Skill drafts (NOT ACTIVE)

Drafted 2026-10-04 by Claude Code. The request arrived as a message from another Claude session, which said
the owner had asked for it; the owner has not confirmed that in this session. These are drafts for the
owner to read. Nothing here is loaded by Claude Code: skills are only picked up from
`.claude/skills/` in the repo or `~/.claude/skills/`, and nothing was put there. No hook, MCP server or
settings change was made.

| Draft | What it is for | How it would start |
|---|---|---|
| `jarvis-verify/SKILL.md` | Prove a Core, desktop or release change works before it is called done: the four test suites, one real launch, the packaged build, with pasted output as evidence | By itself when work is about to be reported as done, or `/jarvis-verify` |
| `jarvis-owner-gate/SKILL.md` | Check a planned action against the OWNER-ONLY list and the standing rules; stop and ask when the owner is needed | By itself before risky actions, or `/jarvis-owner-gate` |
| `jarvis-codex-review-brief/SKILL.md` | Write a tightly scoped brief for Codex as an independent reviewer | Only when typed: `/jarvis-codex-review-brief` |

## To activate (owner decision)

`CLAUDE.md` gives standing authority to edit the repo and maintain `.claude/settings.json`, but says nothing
about skills, so activation is the owner's call. For each skill the owner wants:

1. Say which of the three to activate.
2. Claude copies that folder to `.claude/skills/<name>/` and commits it. It is live from the next session.
3. Removing the folder turns it off again.

Optional and separate: a hook that enforces the owner-gate rules mechanically. Not drafted; it needs its own
approval, and the deny rules in `.claude/settings.json` already block the most dangerous commands.

## Where the content came from

- OWNER-ONLY list and roles: `CLAUDE.md`, copied word for word.
- Standing rules: `../governance/OWNER-DELEGATION.md`, `docs/CURRENT-STATUS.md`, `../governance/LIVE-INSTALLATION-MAP.md`.
- Test, run and build commands: `docs/DEV-SETUP.md` and the Commands section of `docs/CURRENT-STATUS.md`.
- Bind address: `server.py` creates its listener on `127.0.0.1`; `phone_bridge.py --host` defaults to `127.0.0.1`.

## Not confirmed (check before relying on a draft)

- **Not tried out.** The drafts were written, not run. No test prompts were executed, so how reliably each
  one starts by itself is unknown.
- **Test totals.** The suites were not run for this drafting. Recorded totals differ by date (271/34/18/16
  in `docs/DEV-SETUP.md`, 316/34/18/16 in `docs/CURRENT-STATUS.md`, 325/36/18/16 for the 1.0.11
  regression), so the verify draft compares against the latest recorded totals instead of fixed numbers.
- **The launch check.** The desktop launch and the files it writes (`data\core-owner.json`,
  `data\logs\core.log`) are taken from `docs/DEV-SETUP.md`, not re-observed. No health address that works
  without the session token was found, so the draft does not call the API.
- **`allowed-tools` and `disable-model-invocation`.** Written from memory of the Claude Code documentation,
  not checked against the installed version. As understood, `allowed-tools` lets the listed tools run
  without a permission prompt while the skill is active; it does not block other tools, which stay under
  `.claude/settings.json`. The lists are therefore read-only tools only, so they pre-approve nothing that
  can change anything. If the installed version treats the list as a strict limit instead, `jarvis-verify`
  needs the test and launch commands added before it can run them.
- **Codex brief location.** No existing convention for review briefs was found; `docs/codex-reviews/` is a
  proposal. How the owner passes a brief to Codex is the owner's choice.
