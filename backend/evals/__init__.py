"""Offline behavioral evals for the agent harness.

Each scenario drives the real PlanActFlow with a scripted LLM and fake
externals (from ``tests.harness``), then scores the resulting event stream
and agent memories against behavioral checks. Run with:

    cd backend && uv run python -m evals.run
"""
