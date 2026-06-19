# floe-crewai-starter

[![guarded by floe-guard](https://img.shields.io/badge/guarded%20by-floe--guard-2f81f7.svg)](https://github.com/Floe-Labs/floe-guard)
[![CI](https://github.com/Floe-Labs/floe-crewai-starter/actions/workflows/ci.yml/badge.svg)](https://github.com/Floe-Labs/floe-crewai-starter/actions/workflows/ci.yml)

**A governed CrewAI agent, clone-and-run.** A CrewAI crew whose spend is
hard-capped by [floe-guard](https://github.com/Floe-Labs/floe-guard) out of the
box. The 3 AM infinite loop dies at **$1**, not **$400**.

CrewAI's most expensive failure mode is the runaway loop — an agent re-feeds its
growing scratchpad into the next call, costs climb every turn, and no one is
awake to stop it. This starter ships the stop.

## See it stop a loop (no API key needed)

The killer first impression takes seconds and needs **no API key, no account, no
network**:

```bash
pip install -r requirements.txt
python demo.py
```

You'll watch a runaway loop's spend climb turn by turn, then floe-guard
hard-stop it the moment the next call would cross the ceiling:

```
A CrewAI agent is stuck in a runaway loop. Budget ceiling: $1.00.
Each turn re-sends the whole growing transcript, so every call costs more.

  turn # 1: +$0.0130  (running total $0.0130 / $1.00)
  ...
  turn #18: +$0.0980  (running total $0.9990 / $1.00)

floe-guard HARD-STOPPED the loop before turn #19.
  spent $0.9990 of the $1.00 ceiling — the next call would have crossed it, so it never ran.
  The 3 AM infinite loop dies here, not at $400.
```

The "LLM" here is a stub with growing token usage — priced offline from
floe-guard's bundled cost map. No crewai, no litellm, no key needed.

## Run on Replit

[![Run on Replit](https://replit.com/badge/github/Floe-Labs/floe-crewai-starter)](https://replit.com/new/github/Floe-Labs/floe-crewai-starter)

The Run button executes `python demo.py` — the zero-key budget demo, no secrets
needed. Add `OPENAI_API_KEY` in the Secrets tab to run the real crew.

## Use this template

Click **"Use this template" → "Create a new repository"** at the top of the
[GitHub repo](https://github.com/Floe-Labs/floe-crewai-starter) to get your own
copy, then clone and run.

## Run the real governed crew

Once you have an LLM key:

```bash
cp .env.example .env       # then add your OPENAI_API_KEY
python crew.py
```

`crew.py` is a minimal two-agent crew (a Researcher and a Writer). One line caps
the whole crew:

```python
from floe_guard import BudgetGuard
from floe_guard.integrations.crewai import guard_crew

guard = BudgetGuard(limit_usd=1.00)
guard_crew(guard)          # one line — enforces across every agent and task
Crew(agents=[...], tasks=[...]).kickoff()
```

CrewAI runs every agent step through LiteLLM, so a single budget callback meters
the entire crew under one ceiling (default **$1.00**, override with
`FLOE_BUDGET_USD`). The call that would cross it raises `BudgetExceeded` before
it runs.

### Optional: one-env-var hosted upgrade

Set `FLOE_API_KEY` and `crew.py` reads your agent's **server-side remaining
budget** from Floe's credit API and tightens the local ceiling to it. Get a key
at the [Floe dashboard](https://dev-dashboard.floelabs.xyz/?utm_source=floe-crewai-starter&utm_medium=readme&utm_campaign=template).

Honest framing: this **reads** your remaining budget to inform the local cap. It
does not move enforcement server-side by itself, and it fails safe to the local
cap on any error. (The read helper ships in newer floe-guard releases; if your
installed version predates it, the script says so and uses the local cap.)

## Honest scope

This starter ships the **local** floe-guard. Be clear about what that means:

- **What it does:** prices token usage offline (from floe-guard's bundled cost
  map) and hard-stops your crew *in-process* before a call crosses the ceiling.
  No network, on by default.
- **What it is not:** the local guard is **estimate-based and in-process**. It
  caps the LLM calls that run through this crew's LiteLLM path. It is not a
  server-side, un-bypassable cross-vendor cap. The `FLOE_API_KEY` upgrade only
  *reads* your remaining budget to tighten the local ceiling; it does not enforce
  on Floe's side.
- **Un-bypassable, cross-vendor enforcement** (caps that hold no matter which
  process or vendor spends — LLM tokens *and* paid x402 tool calls) is the hosted
  [Floe](https://floelabs.xyz/?utm_source=floe-crewai-starter&utm_medium=readme&utm_campaign=template)
  product.

## Configuration

| Env var | Required | Default | Purpose |
| --- | --- | --- | --- |
| `OPENAI_API_KEY` | for the real crew | — | OpenAI key for `crew.py`. The demo needs none. |
| `FLOE_BUDGET_USD` | no | `1.00` | Local spend ceiling in USD. |
| `FLOE_API_KEY` | no | — | Read-only hosted budget tightening. |
| `CREW_TOPIC` | no | a default topic | The topic the crew researches and summarizes. |

## Built with floe-guard

[![guarded by floe-guard](https://img.shields.io/badge/guarded%20by-floe--guard-2f81f7.svg)](https://github.com/Floe-Labs/floe-guard)

```markdown
[![guarded by floe-guard](https://img.shields.io/badge/guarded%20by-floe--guard-2f81f7.svg)](https://github.com/Floe-Labs/floe-guard)
```

## License

MIT — see [LICENSE](./LICENSE).
