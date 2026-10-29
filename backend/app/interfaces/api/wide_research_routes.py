"""Wide Research routes — parallel research endpoint.

Manus Wide Research: https://manus.im/docs/features/wide-research
Decomposes a goal into independent items and runs sub-agents in parallel.

Endpoint: POST /api/v1/wide-research
"""

from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.interfaces.dependencies import get_current_user
from app.domain.models.user import User

router = APIRouter(prefix="/wide-research", tags=["wide-research"])


class WideResearchRequest(BaseModel):
    goal: str
    items: List[str]  # e.g. 100 product names, 250 researcher names
    max_parallel: int = 3


class WideResearchResponse(BaseModel):
    goal: str
    tasks_created: int
    tasks: List[dict]


@router.post("", response_model=dict)
async def create_wide_research(
    req: WideResearchRequest,
    current_user: User = Depends(get_current_user),
):
    # Scaffold: returns decomposition preview; actual fan-out happens via
    # WideResearchCoordinator when wired to a session execution.
    # This endpoint is intentionally lightweight for quota safety.
    tasks = [
        {"id": f"wr-{i}", "query": q, "description": f"Research '{q}' for goal: {req.goal}"}
        for i, q in enumerate(req.items[:250])  # Manus claims up to 250, we allow same
    ]

    return {
        "code": 0,
        "msg": "success",
        "data": {
            "goal": req.goal,
            "tasks_created": len(tasks),
            "max_parallel": req.max_parallel,
            "tasks": tasks,
            "note": "Wide Research executes via WideResearchCoordinator — integrate with PlanActFlow for full run. See backend/app/domain/services/flows/wide_research.py",
        },
    }


@router.get("/health", response_model=dict)
async def health():
    return {"code": 0, "msg": "success", "data": {"status": "ok", "max_items": 250}}
