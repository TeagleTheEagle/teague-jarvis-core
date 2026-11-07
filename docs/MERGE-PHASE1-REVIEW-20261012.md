# Merge plan phase 1 (OpenRouter in the Core): independent review record

**Date:** 2026-10-12. **Branch:** `claude/veronica-merge`. **Scope:** the OpenRouter work of
`docs/VERONICA-MERGE-PLAN.md` phase 1 (decisions D2, D6, D7, D8): a third provider `openrouter` in `providers.py`,
its use in `actions.py` (web search), `connection_checks.py`, `server.py` (missions, picture description, the
question loop, interface inspection), the Settings view, and `test_openrouter_provider.py` (34 tests).

The code written earlier in the day carried comments citing "review of 2026-10-12" findings (H1, M1, M2, M3, L1,
L2, L4), but no record of that review was found and the work had not been committed. This is the record of the
independent review run before the commit; it covers those citations and supersedes them.

## The reviewer's findings and what was done

**High**
- **H1 — the backup model could be reached even with Settings > AI > Backup off.** `providers.chat` and
  `openrouter_chat` defaulted `fallback=True`, and the interface-inspection picture call did not pass the owner's
  switch, so it always sent the `models` fallback list. With Backup off and sending allowed, a failed primary could
  send screenshots to the backup model's company with no note.
  **Fixed:** the default is now `fallback=False` (safe), and `App.fallback_option` returns `{'fallback': True}` only
  when OpenRouter is chosen and Backup is on. Every Core call opts in through `fallback_option`; a caller that forgets
  it, including the inspection call and any future one, reaches no backup model. Tests:
  `test_with_backup_off_no_request_offers_the_backup_model`, `test_with_backup_on_the_request_offers_the_backup_model`,
  `test_a_mission_step_uses_the_coding_model_and_honours_backup`.

**Medium**
- **M2 (this review) — a picture description written by the backup model did not tell the owner.**
  `describe_picture`'s result is a tool result that goes back to the model, and `claim_checks` strips the Core's note
  from the model's reply, so the owner was never told. **Fixed:** the note is kept off the tool data and stashed on
  the run (`run.nested_fallback_note`), `describe_picture` records it in the activity log and emits `provider.backup`,
  and `App.work` adds the Core's own note to the final reply. Test:
  `test_a_backup_described_picture_tells_the_owner_and_stays_out_of_the_tool_data`.
- **M (this review) — no server-level test that Backup off is honoured.** Only the provider call was covered.
  **Fixed:** the run-level, mission and picture tests above assert no request body carries `models` when Backup is
  off (the one-piece retry reuses the same options), and that it does when Backup is on.

**The two test corrections made before the review**
- `is_fallback('x/m', 'x/m-fast', 'x/m')` is **True**: OpenRouter can report a shorter name for the asked model, so a
  reply naming the backup model's own name exactly means the backup answered. The reviewer confirmed the code was
  right and the old test wrong; "never fall back silently" settles the tie in favour of disclosing.
- `capabilities()['backup']` **names** OpenRouter's backup model (and is `None` when `OPENROUTER_FALLBACK_MODEL` is
  empty). Backup ships on, so Settings must not imply the question cannot reach another company. Confirmed right.

## Confirmed safe by the review
- The OpenRouter base address is fixed (`openrouter.ai`); the key is only ever sent there; redirects are refused for
  requests carrying a key; neither the `/key` reply nor error bodies are shown or passed on.
- Backup off is honoured on every path: the question loop (streamed and the one-piece retry), missions,
  `describe_picture`, and the connection tests; web search and speech-to-text never use a backup model.
- The Core, never the model, says when the backup model answered; `BACKUP_NOTE` strips the note from replies, drafts
  and history.
- No regression on the `openai` and `qwen` paths: `chat_options` is unchanged for them, the Qwen request body and
  argument order are unchanged, and the new four-value stream result has a single caller.

## Left for later (not blockers; recorded so they are not lost)
- **L4 (coding pair, same maker).** Opus with Sonnet as the backup are both Anthropic; if OpenRouter returns reordered
  official names, a Sonnet-written mission step may not be detected as a fallback. No data goes to another company.
  Fix when the official names are known (from `/api/v1/models`) or by comparing name parts without dates.
- A mission step taken over by the backup model is recorded only in the activity log, not the mission log or chat.
- When both the primary and the backup model fail, the error does not say the backup was tried.
- Live checks for the owner's function test (plan item 6): "think hard" high effort against the 16,384-token / 120 s
  limits; a tool loop where the backup model takes over partway with thinking on; the real per-search cost and the
  quality of the one-line search query.
- The Settings wording when `OPENROUTER_FALLBACK_MODEL` is empty, and naming the backup model's company in the Backup
  help text.
- Deferred by the plan until the owner's live test: removing the old providers and the offline-answer path (D8).
