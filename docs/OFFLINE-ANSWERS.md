# Answers without the internet (release 1.0.15, scope item 7)

Built 2026-10-06 in the repo only. Master document section 16: JARVIS stays useful when the internet is gone.

**Before:** with no connection to the AI provider a question simply failed ("Connection failed"). A local model
runtime (Ollama) was only ever used to label commands for a log; it never answered anyone.

**Nothing here installs or downloads anything.** The feature does something only on a PC that has the program
Ollama with a chat model. **The owner's PC has both** (found on 2026-10-06: Ollama is running there with the models
`qwen3:4b` and `llama3.2`), so with 1.0.15 a question asked while no provider can be reached is answered by the local
model, unless the owner unticks Settings > AI > Offline answers. Without Ollama a question without a connection
fails exactly as before.

## 1. What happens

When the chosen AI provider **cannot be reached**, and the backup provider cannot be reached either or is switched
off, and a local model is installed, the Core asks that model on this PC (`127.0.0.1:11434`, nothing leaves the PC)
and gives its answer. "Cannot be reached" means that no answer came back over the connection at all: no connection,
a name that cannot be looked up, a blocked or failed secure connection, a timeout, also a provider that took the
question and then never answered or closed the connection. It never means a refusal (section 2). The reply ends with a line that
only the Core can write:

> [Answered offline by the local model qwen3:4b on this PC. Qwen chat: Connection failed. It cannot use tools or
> look anything up, and it is less accurate than the usual provider.]

The local model gets a small request made for a small model (`offline_answers.py`): short instructions that say
what it cannot do, the owner's preferred name and answer length, at most eight saved facts that fit the question,
and the recent plain conversation (about 3,000 characters). No tools, no pictures, no files.

## 2. When it does not answer (and the provider's own error stands, unchanged)

- **A refusal is not "no internet".** An unpaid bill, a wrong key, a rate limit or a model the account may not use
  is the owner's to see and fix; the local model does not answer around it.
- A picture or a file came with the question (the local model sees neither).
- A tool already ran in this question (nothing is answered around something half done).
- The owner switched it off: Settings > AI > "Offline answers" (on by default; it does nothing without Ollama).
- Ollama is not running, or the model is not installed, or it gave no usable answer within 90 seconds.

Typed and spoken commands that never needed a provider (timers, notes, saved facts, opening a section) work
without the internet as they always did.

## 3. What it needs (already there on the owner's PC)

1. The program Ollama, running (a system-wide install: the owner's act; on this PC it is installed).
2. The model `qwen3:4b` in it (`ollama pull qwen3:4b`; on this PC it is there). Another model can be named with the
   key-file line `JARVIS_OFFLINE_MODEL=<name>` (with or without `:latest`). This PC also has `llama3.2`, but in the
   review it was too slow here: 90 seconds and no answer the first time, 53 seconds the second. A model that Ollama
   runs on its own servers ("cloud" models) is never used: an offline answer does not leave this PC.
3. Settings > AI > Offline answers then says "Ready: the local model qwen3:4b is installed."

A small model on a PC without a strong graphics card is slow (the first answer also loads the model) and it makes
mistakes a large model does not. It is a fallback for when nothing else answers, and says so every time.

## 4. Rules

- **A model's thinking is never shown as the answer.** `qwen3:4b` on the owner's PC writes its thinking first and
  closes it with `</think>` (no opening tag, and asking it not to think changes nothing: seen in a real run). Such
  models are therefore asked to hand their thinking over separately (`"think": true`; Ollama then returns a clean
  answer, seen with the same model), and as a second defence only what follows the last `</think>` counts as the
  answer; an answer cut short before that point counts as no answer.
- **The local model's words meet the same checks as a provider's** (`App.claim_checks`): "I have saved the note"
  without a receipt becomes "No matching action result was recorded…", "the tests passed" needs the result on
  record. A small model that cannot do anything must not be the one that gets to claim it did.
- **Stop ends a local answer at once** (its connection is closed, so the model stops working on it), and a question
  that was stopped while the provider was still being tried asks nobody.
- Whatever goes wrong on the offline path itself, the provider's own error stands as it was (activity row "offline
  answer / failed"); it never becomes "failed internally".
- Only the Core writes the closing line: it is removed from anything a model writes (the local one or a
  provider's), in any letter case and over line breaks, and from earlier replies before they are sent to a model
  again. The same holds for the backup provider's line, in both directions. (A saved reply read back through a
  tool, such as a project's conversation, still shows the line to the provider; what the provider then writes is
  filtered all the same.)
- The answer is saved in the conversation like any reply, with its closing line. The activity log has a row
  "offline answer: <model> / used" for each one.
- Speech: with no internet a cloud voice (Qwen, Fish) cannot speak. The reply is shown on screen and a short
  message says that the voice is unavailable. A voice that works offline is not part of this item.
- `GET /api/offline-answers` (the owner's session) tells Settings whether a local answer is possible right now; it
  asks only this PC and gives up after a second.

## 5. Checked

`test_offline_answers.py` (18 tests: when a local answer is possible; the small request; a plain answer; a model's
thinking never shown, from the real output of the owner's model; no answer said plainly; nothing asked without
Ollama or the model; the closing line; the review's cases of section 6), `test_offline_core.py` (14 tests through
the Core's real answer path with stand-ins for the provider and for Ollama, the review's cases among them: the local model answers when no provider can be reached, also when
neither can; a cut-short answer says so; only the Core says who answered; never for a refusal, when switched off,
without Ollama or the model, after a tool has run, for a picture, or when the backup provider answers; the route
for Settings).

**With the real local model on this PC** (sandbox Core, synthetic data, a made-up key, every outgoing connection
pointed at a dead local port so that nothing could leave the PC): a typed question was answered by `qwen3:4b` in
about 18 seconds from pressing Enter (two connection attempts with a pause first, then the model), the reply ended
with the closing line, and the activity log had its row. The first such run showed the model's thinking in the
reply; that is what the rule above fixes, and the second run showed the answer only.

Not checked: a real loss of the internet with the real provider key (the same code path, reached by a different
cause); speech for an offline answer; how good the small model's answers are beyond that one question.

## 6. Independent review (2026-10-06, one reviewer): no high finding, 2 medium, 5 low, all applied

The reviewer ran its own experiments with stand-ins and asked the real local models on this PC six times.

| | Found | Done |
| --- | --- | --- |
| B1 medium | Stop and the emergency stop did not end a local answer: the wait (up to 90 seconds) went on, and a new question was refused meanwhile. A question stopped during the provider's second try still asked the local model. | Stop ends the wait and closes the connection; a stopped question asks nobody. |
| B2 medium | The claim checks were not applied to the local model's text: "I have saved the note and the timer has been scheduled" was shown as written, saved, and later sent to the provider as if the provider had said it. | The same checks as for a provider's answer, through one function. |
| B3 low | An odd reply from Ollama (`"models": null`) turned the provider's clear error into "The request failed internally", and the Settings line into an error. | Read without trusting its shape; any failure on this path leaves the provider's error standing. |
| B4 low | "Only the Core can write the line" held for the exact one-line form only; the backup provider's line was neither removed from the local model's text nor kept from its reading. | Both lines recognised in any case and over line breaks; both removed in both directions. |
| B5 low | Thinking could still show: models named with a prefix (`hf.co/…/Qwen3-…`) were not recognised as thinking models, and `</THINK>` was not recognised. | The name is searched anywhere; thinking models are asked to hand the thinking over separately; the closing mark in any case. Left as it is: a model that stops by itself in the middle of its thinking with no closing mark cannot be told from an answer. |
| B6 low | "Could not be reached" in the code is wider than this record said (a provider that took the question and never answered counts too); one OpenAI time-limit error lost the mark. | Section 1 says what it means; the time-limit error keeps the mark. |
| B7 low | `JARVIS_OFFLINE_MODEL=llama3.2` (no `:latest`) was reported as not installed; `llama3.2` is very slow on this PC; a cloud model named there would have sent the question away while the line said "on this PC". | The short name is accepted; the slowness is said in section 3; a cloud model is never used. |

The fixes were not reviewed again.
