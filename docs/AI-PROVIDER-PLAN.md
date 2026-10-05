# AI provider plan: Qwen for all of JARVIS

Status: **owner decision 2026-10-05: "i want qwen to be the api we use"** (and: "let's not minimise or make jarvis
less"). Nothing in JARVIS or the key file has changed yet. The steps marked "you" are account, billing and key-file
steps, which only you can do; Claude never opens the key file.

## Why a change is needed

After the update to 1.0.14 JARVIS answered a real question with "Groq returned HTTP 413". The owner-run check
(`tools/host/Test-AiKeys.ps1`, 2026-10-05) showed why, and the state of every provider in the key file:

| Provider | Result | Meaning |
|---|---|---|
| Groq (`openai/gpt-oss-120b`, free tier) | small request works; a JARVIS-sized one is refused: "Limit 8000, Requested 13006" | the free tier allows 8,000 tokens per minute and 200,000 per day; one JARVIS question is about 12,000-13,000 |
| OpenAI (`gpt-6-astra`) | no credits | and at $10 / $50 per million tokens it would cost about $400 a month at normal use |
| Gemini (`gemini-3.8-flash`) | prepaid credits used up | |
| Qwen (`qwen3.8-max`) | `AccessDenied.Unpurchased` | Model Studio is not activated or paid for on the account yet |

JARVIS is not cut down to fit a free tier: its instructions and the descriptions of its 45 tools (about 10,000 tokens)
go with every question so that it can use all of its abilities. This was the same in 1.0.11.

## What Qwen covers

| JARVIS job | With this plan | Key-file line (you) |
|---|---|---|
| Thinking and tools: conversation, briefings, tasks, memory, research, files, projects | Qwen `qwen3.8-max` (Alibaba's flagship, 1 million token window, 131,072-token answers) | `JARVIS_PROVIDER=qwen` (the model defaults to `qwen3.8-max`) |
| Vision: screen vision, images you attach | the same `qwen3.8-max` (it reads images and video) | `QWEN_VISION_MODEL=qwen3.8-max` |
| Speaking (JARVIS's voice) | stays **Fish Audio**, which works today | none |
| Listening (speech to text) | stays on this PC (offline Whisper); the cloud fallback stays Groq's free Whisper | none |
| Web search, YouTube, Maps, Spotify | unchanged (separate services) | none |

Later, if you want everything on one Alibaba bill: JARVIS can also speak with a Qwen **cloned voice** (already built:
`QWEN_TTS_VOICE`, model `qwen3-tts-vc-2026-01-22`). It needs a voice sample enrolled in Model Studio and a one-time
unlock fee of CNY 9.9 per voice, then a price per character. Not part of this first step.

## Cost (estimates; Alibaba bills what is used)

Price of `qwen3.8-max` (Singapore / international, Alibaba's model page, October 2026): **$2 per million input tokens,
$6 per million output tokens; repeated input (implicit cache) $0.25 per million**. Rate limits rise with spend and are
far above one person's use; the 1 million token window means size is never the problem again.

Assumed: one question = about 2 AI calls of about 12,500 tokens in (about 10,000 of them the same instructions and tool
list each time, which Alibaba's cache bills at the lower rate) and 300 out.

| Use | Questions | Qwen per month (cache working) | if the cache misses |
|---|---|---|---|
| light | 20 a day | about $11 | about $32 |
| normal | 50 a day | about $28 | about $80 |
| heavy | 150 a day | about $84 | about $240 |

Extra: live screen sharing sends a picture every few seconds, roughly $1 for 10 minutes; Fish Audio voice at $15 per
million characters is about $4 / $9 / $27 a month for the three uses above if every answer is spoken. New Model Studio
accounts get 1 million free tokens per model for 90 days (about 40 questions). Suggested: a **budget alert of $40 a
month** in Alibaba Cloud billing; raise it once you know your real use.

## What the owner's console showed (2026-10-05, screenshots)

- **Expenses and Costs:** available credit **-25.08 USD, Overdue**; the September 2026 bill (22.80 USD + 2.28 USD
  tax) is unpaid. Alibaba's error-code page names an inactive or unpaid service as the cause of
  `AccessDenied.Unpurchased`: **this overdue bill is the block.**
- **API key permissions** (Model Studio, Singapore, default workspace): the key may already use `Qwen3.8-Max`,
  `Qwen3.8-Flash`, `qwen3-asr-flash`, `cosyvoice-v3-flash`, `qwen-audio-3.0-tts-flash`, `qwen3-tts-vc-2026-01-…` and
  `qwen-voice-enrollment`. Nothing to change there.
- **Token Plan** ($6 / $10 / $18 / $68 a month subscriptions): **not for JARVIS.** Alibaba's FAQ: Token Plan
  Personal Edition "is only for individual interactive development through officially designated tools (such as
  Cursor, Claude Code, and Windsurf). Using the API Key for production automated services, batch scripts, scheduled
  background tasks, or other non-interactive scenarios is not allowed." It also needs its own `sk-sp-` key and
  address. JARVIS uses ordinary pay-as-you-go with the existing key.
- **Other ways to pay (checked 2026-10-05, owner asked for a subscription):** none is worth it for JARVIS. The AI
  General-purpose Savings Plan (10-32% off, usable for API calls) starts at a USD 150 monthly commitment for 3 to 24
  months, above JARVIS's expected cost; the smaller "Other Model Savings Plans" (USD 10, 50, 100, ...; 3-6 months)
  give no discount (standard prices, prepaid). Source: Alibaba Cloud help, "savings-plan-and-resource-package".
  Cheaper model for a later side-by-side test, only on the owner's word (the owner does not want JARVIS made less):
  Qwen3.7-Plus, $0.40 in / $1.60 out per million up to 256K tokens (limited-time 20% off; not in the key's current
  permission list).
- **One key for every AI company (owner asked 2026-10-05, "like claude, chatgbt?"):** OpenRouter (openrouter.ai)
  sells one prepaid key for Qwen, Claude, GPT, Gemini and others at the companies' own prices plus a 5.5% fee on
  credit purchases (minimum $0.80); credits do not expire, so no overdue bills. `qwen/qwen3.8-max` is listed there at
  $2 / $6 with tools and vision. A Claude Pro or ChatGPT Plus subscription gives no API key for an app. JARVIS cannot
  use OpenRouter today: the Qwen provider accepts only `*.aliyuncs.com` addresses (`providers.py`), so it needs a new
  provider in a release (tests, Stage 7 check, owner approval). Fish Audio voice and local Whisper stay as they are.
  Not started; the owner decides.
- **Anthropic (owner asked 2026-10-05, "does anthropic offer api keys?"):** yes, through the Claude Console with
  prepaid credits, separate from a Claude Pro/Max subscription. Prices per million tokens in / out (cache reads):
  Claude Sonnet 5.5 $2 / $10 ($0.20), Claude Opus 5.5 $4 / $20 ($0.20), Claude Haiku 4.5 $1 / $5. All read images and
  use tools. JARVIS has no Claude provider: it needs a new provider in a release (Anthropic Messages API, explicit
  `cache_control` for caching). Also reachable through OpenRouter. Not started; the owner decides.
- **Voice (owner, 2026-10-05): "i want to use qwen now not fish auido".** Already built, no release needed: the key
  file needs `QWEN_TTS_VOICE=<cloned voice ID>` (and `QWEN_TTS_MODEL` only if the voice was enrolled for a model other
  than `qwen3-tts-vc-2026-01-22`), then Settings > VOICE PREVIEW > "Qwen — cloned JARVIS voice" > USE THIS VOICE. A
  cloned voice belongs to the Alibaba account that enrolled it. Open: whether a voice ID exists on the current account
  (the console's API Key page shows one key, created 2026-09-18, Singapore, default workspace); if not, a voice sample
  must be enrolled (owner-run tool, not written yet). Fish lines stay in the file so the owner can switch back.
  Console notice seen: `dashscope.aliyuncs.com` enters maintenance mode from 2026-09-30 and keeps working; check
  whether `dashscope-intl` is affected in the next release.

## Your steps (Alibaba Cloud console, your own account)

1. **Expenses and Costs:** optionally open **Bill Details** for 2026-09 to see what the 22.80 USD was for; then
   **Pay Bill** (25.08 USD) and wait a few minutes until the account is no longer overdue.
2. **Budgets** (same page, left menu): a monthly budget alert, for example $40.
3. Do **not** subscribe to a Token Plan for JARVIS (see above).
4. **API key:** keep the existing key (`DASHSCOPE_API_KEY`, starting `sk-`); its permissions already include
   `qwen3.8-max`. If identity verification is still pending and Alibaba asks for it, finish it.
5. **Check** (jonny account, Command Prompt), the same command as today:
   `powershell -ExecutionPolicy Bypass -File C:\Users\jonny\JARVIS-claude-workspace\repo\tools\host\Test-AiKeys.ps1`.
   It now sends Qwen one exact JARVIS request (its instructions, its 45 tools, JARVIS's own settings) and a question
   that needs a tool. Wanted: `qwen    WORKS` and `qwen    HANDLES IT: asked for the tool time_now`. Send Claude a
   photo either way.
6. **Key file** (only after step 5 passes): Claude gives you the exact two lines to add or change, and where.
7. Quit JARVIS completely (icon near the clock), start it again, and check: Settings shows "Qwen configured"; ask
   "what's on today?"; say "analyse my screen".

## Claude's part

- Done (2026-10-05): `Test-AiKeys.ps1` tests a full JARVIS request per provider (`tools/host/jarvis-request-*`, written
  from the code by `tools/host/make_request_template.py`), tested with a fake key file.
- If step 5 shows a problem in JARVIS's own Qwen code (for example a setting Qwen rejects), Claude fixes it in the
  next release (1.0.15) through the usual checks, before you switch.
- Next release, in any case: plain messages for "request too large" (HTTP 413) and "model not activated"
  (`AccessDenied.Unpurchased`) instead of "check your key"; the Settings connection check sends a full-size request,
  not a tiny one.

## Not chosen (for the record)

Groq Developer tier (card on file, $0.15 / $0.60 per million, 250,000 tokens per minute: the cheapest way to make
today's setup work); Gemini 3.8 Flash ($0.75 / $3.75 per million until 31 December 2026, then $1.50 / $7.50; needs
the prepay topped up); OpenAI GPT-6 Astra ($10 / $50); Claude (would need a new adapter in JARVIS). The Groq key
stays in the file for speech-to-text.

## Sources (October 2026)

Alibaba Cloud Model Studio, qwen3.8-max model page (https://www.alibabacloud.com/help/en/model-studio/qwen3-8-max) and
error codes (https://www.alibabacloud.com/help/en/model-studio/error-code); Groq rate limits
(https://console.groq.com/docs/rate-limits) and models (https://console.groq.com/docs/models); Fish Audio API pricing
(https://docs.fish.audio/developer-guide/models-pricing/pricing-and-rate-limits); secondary price summaries for
GPT-6 Astra, Gemini 3.8 Flash and Qwen TTS (CloudZero, layer3labs, benchlm, wavespeed).
