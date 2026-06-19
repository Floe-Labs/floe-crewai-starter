"""crew.py — a real, budget-governed CrewAI crew.

A minimal two-agent crew (a Researcher and a Writer) with a hard spend ceiling
wired in by default. One line — ``guard_crew(guard)`` — caps the WHOLE crew:
CrewAI runs every agent step through LiteLLM, so a single budget callback meters
every agent and every task under one ceiling. If the crew would cross it, the
next LLM call is refused (``BudgetExceeded``) instead of running.

Run it (needs an LLM key)::

    export OPENAI_API_KEY=sk-...
    python crew.py

The ceiling defaults to $1.00; override with FLOE_BUDGET_USD.

Optional hosted upgrade
-----------------------
If FLOE_API_KEY is set, this script *reads* your agent's server-side remaining
budget from Floe's credit API and tightens the local cap to it. Be honest about
what that is: the read only INFORMS the local, in-process ceiling. The
un-bypassable, cross-vendor enforcement is the hosted Floe product running
server-side — not this script. Any read failure falls back safely to the local
cap. (The read helper ships in newer floe-guard releases; if your installed
version doesn't have it yet, the script says so and uses the local cap.)
"""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

from floe_guard import BudgetExceeded, BudgetGuard
from floe_guard.hosted import hosted_enforcement_available
from floe_guard.integrations.crewai import guard_crew

# The hosted *read* helper (hosted_remaining_usd) and HostedEnforcementError ship
# in newer floe-guard releases. Feature-detect them so the starter works on the
# currently-published package today and auto-upgrades when they land — no
# fabricated API, no hard dependency on an unreleased symbol.
try:
    from floe_guard.errors import HostedEnforcementError
    from floe_guard.hosted import hosted_remaining_usd

    _HOSTED_READ_AVAILABLE = True
except ImportError:  # installed floe-guard predates the hosted read helper
    _HOSTED_READ_AVAILABLE = False

load_dotenv()

MODEL = "gpt-4o"


def _local_budget_usd() -> float:
    """The local spend ceiling. Defaults to $1.00; override with FLOE_BUDGET_USD."""
    raw = os.environ.get("FLOE_BUDGET_USD", "").strip()
    if not raw:
        return 1.00
    try:
        value = float(raw)
    except ValueError:
        return 1.00
    return value if value >= 0 else 1.00


def _resolve_ceiling() -> float:
    """Pick the spend ceiling, tightening to hosted remaining budget if available.

    Always fail safe to the local cap: a missing key, an old floe-guard without
    the read helper, or any hosted error must never *raise* the budget — it can
    only lower it.
    """
    local_cap = _local_budget_usd()

    if not hosted_enforcement_available():
        return local_cap

    if not _HOSTED_READ_AVAILABLE:
        print(
            "FLOE_API_KEY is set, but the installed floe-guard does not include the "
            "hosted read helper (hosted_remaining_usd). Upgrade floe-guard to read "
            f"server-side remaining budget. Using the local ${local_cap:.2f} cap.\n"
        )
        return local_cap

    try:
        remaining = hosted_remaining_usd()
    except HostedEnforcementError as exc:
        print(
            f"Could not read hosted Floe budget ({exc}). "
            f"Falling back to the local ${local_cap:.2f} cap.\n"
        )
        return local_cap

    ceiling = min(local_cap, remaining)
    print(
        f"Hosted Floe reports ${remaining:.2f} remaining; tightening the ceiling "
        f"to ${ceiling:.2f} (min of local cap and hosted remaining).\n"
        "Note: this READS your server-side budget to inform the local cap. "
        "Un-bypassable cross-vendor enforcement is the hosted Floe product.\n"
    )
    return ceiling


def build_crew(model: str = MODEL):
    """Build a minimal two-agent research-and-write crew.

    Imported lazily inside main() so the module imports cleanly without crewai's
    heavier dependencies being exercised until a run is actually requested.
    """
    from crewai import LLM, Agent, Crew, Process, Task

    llm = LLM(model=model)

    researcher = Agent(
        role="Researcher",
        goal="Find the three most important, concrete facts about the topic.",
        backstory="A concise analyst who cites specifics and never pads.",
        llm=llm,
        verbose=True,
    )
    writer = Agent(
        role="Writer",
        goal="Turn the research into a tight, three-sentence summary.",
        backstory="An editor who values clarity and brevity over length.",
        llm=llm,
        verbose=True,
    )

    topic = os.environ.get("CREW_TOPIC", "why AI agents need spend governance").strip()

    research_task = Task(
        description=f"Research the topic: {topic}. List three concrete facts.",
        expected_output="Three bullet points, each a concrete, specific fact.",
        agent=researcher,
    )
    write_task = Task(
        description="Write a three-sentence summary from the research bullets.",
        expected_output="Exactly three sentences, no preamble.",
        agent=writer,
        context=[research_task],
    )

    return Crew(
        agents=[researcher, writer],
        tasks=[research_task, write_task],
        process=Process.sequential,
        verbose=True,
    )


def main() -> int:
    if not os.environ.get("OPENAI_API_KEY", "").strip():
        print(
            "OPENAI_API_KEY is not set. The real crew needs an LLM key to run.\n\n"
            "  1. cp .env.example .env\n"
            "  2. add your OpenAI key to .env\n"
            "  3. python crew.py\n\n"
            "No key yet? Run the zero-key budget demo instead: python demo.py"
        )
        return 0

    ceiling = _resolve_ceiling()
    guard = BudgetGuard(limit_usd=ceiling)
    guard_crew(guard)  # one line — caps every agent and task in the crew

    print(f"Running a governed crew with a ${ceiling:.2f} ceiling...\n")
    crew = build_crew()

    try:
        result = crew.kickoff()
    except BudgetExceeded as exc:
        print(
            f"\nfloe-guard stopped the crew at its ${ceiling:.2f} ceiling "
            f"(spent ${exc.spent_usd:.4f}). The crossing call never ran."
        )
        return 0

    print("\n--- Crew result ---")
    print(result)
    print(f"\nSpent ${guard.spent_usd:.4f} of the ${ceiling:.2f} ceiling.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
