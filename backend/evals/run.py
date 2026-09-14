"""Eval runner: drive PlanActFlow offline over every scenario and score it.

Usage (from backend/):

    uv run python -m evals.run             # table report, exit 1 on failure
    uv run python -m evals.run --json out.json
"""

import argparse
import asyncio
import json
import sys

from app.domain.models.message import Message

from evals.metrics import ScenarioResult, build_result
from evals.scenarios import SCENARIOS, Scenario
from tests.harness import FakeAgentRepository, ScriptedLLM, build_plan_act_flow


async def run_scenario(scenario: Scenario) -> ScenarioResult:
    llm = ScriptedLLM(list(scenario.responses))
    repository = FakeAgentRepository()
    flow = build_plan_act_flow(llm, agent_repository=repository)

    events = [
        event async for event in flow.run(Message(message=scenario.user_message))
    ]
    result = build_result(events, llm, repository.memories)
    for name, check in scenario.checks:
        try:
            ok = check(result)
        except Exception as exc:  # a crashing check is a failing check
            ok = False
            name = f"{name} (raised {type(exc).__name__}: {exc})"
        if not ok:
            result.check_failures.append(name)
    return result


def render_report(results: dict[str, ScenarioResult]) -> str:
    lines = [
        "| scenario | pass | llm_calls | tool_calls | replans | repairs | rejections | errors | failed checks |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for name, r in results.items():
        lines.append(
            f"| {name} | {'PASS' if r.passed else 'FAIL'} | {r.llm_calls} "
            f"| {r.tool_calls} | {r.update_plan_calls} | {r.invalid_output_feedback} "
            f"| {r.rejected_complete_step} | {r.error_events} "
            f"| {', '.join(r.check_failures) or '-'} |"
        )
    passed = sum(1 for r in results.values() if r.passed)
    lines.append("")
    lines.append(f"{passed}/{len(results)} scenarios passed")
    return "\n".join(lines)


def to_json(results: dict[str, ScenarioResult]) -> dict:
    return {
        name: {
            "passed": r.passed,
            "llm_calls": r.llm_calls,
            "tool_calls": r.tool_calls,
            "update_plan_calls": r.update_plan_calls,
            "invalid_output_feedback": r.invalid_output_feedback,
            "rejected_complete_step": r.rejected_complete_step,
            "unknown_tool_responses": r.unknown_tool_responses,
            "error_events": r.error_events,
            "event_count": len(r.events),
            "check_failures": r.check_failures,
        }
        for name, r in results.items()
    }


async def main() -> int:
    parser = argparse.ArgumentParser(description="Run agent harness evals")
    parser.add_argument("--json", help="also write results as JSON to this path")
    parser.add_argument(
        "--scenario", action="append", help="run only the named scenario(s)"
    )
    args = parser.parse_args()

    selected = [
        s for s in SCENARIOS if not args.scenario or s.name in args.scenario
    ]
    if not selected:
        print(f"No matching scenarios (available: {[s.name for s in SCENARIOS]})")
        return 2

    results: dict[str, ScenarioResult] = {}
    for scenario in selected:
        results[scenario.name] = await run_scenario(scenario)

    print(render_report(results))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(to_json(results), f, indent=2, ensure_ascii=False)
        print(f"JSON written to {args.json}")

    return 0 if all(r.passed for r in results.values()) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
