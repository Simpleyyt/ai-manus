"""Automation routes — Manus Automations replica (Schedule / Triggered / Advanced).

Provides CRUD for automations. Execution is delegated to Celery beat or
the local asyncio scheduler (see domain/models/automation.py).

This is a scaffold that persists to MongoDB when available. For the purpose
of the replica demo, we keep it minimal and compatible with existing auth.

Endpoints: /api/v1/automations
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.interfaces.dependencies import get_current_user
from app.domain.models.user import User
from app.domain.models.automation import Automation, AutomationSchedule, AutomationStatus, AutomationTriggerType

router = APIRouter(prefix="/automations", tags=["automations"])

# In-memory store for demo (replace with beanie repository in production)
_store: dict[str, Automation] = {}


class AutomationCreateRequest(BaseModel):
    name: str
    task_prompt: str
    trigger_type: AutomationTriggerType = AutomationTriggerType.SCHEDULE
    schedule: Optional[AutomationSchedule] = None
    source: Optional[str] = None
    skill: Optional[str] = None
    project_id: Optional[str] = None


class AutomationResponse(BaseModel):
    id: str
    name: str
    trigger_type: str
    status: str
    task_prompt: str
    schedule: Optional[AutomationSchedule] = None


@router.get("", response_model=dict)
async def list_automations(current_user: User = Depends(get_current_user)):
    items = [a for a in _store.values() if a.user_id == current_user.id]
    return {"code": 0, "msg": "success", "data": [a.model_dump() for a in items]}


@router.post("", response_model=dict)
async def create_automation(
    req: AutomationCreateRequest,
    current_user: User = Depends(get_current_user),
):
    automation = Automation(
        user_id=current_user.id,
        name=req.name,
        task_prompt=req.task_prompt,
        trigger_type=req.trigger_type,
        schedule=req.schedule,
        source=req.source,
        skill=req.skill,
        project_id=req.project_id,
    )
    _store[automation.id] = automation
    return {"code": 0, "msg": "success", "data": automation.model_dump()}


@router.get("/{automation_id}", response_model=dict)
async def get_automation(automation_id: str, current_user: User = Depends(get_current_user)):
    item = _store.get(automation_id)
    if not item or item.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Automation not found")
    return {"code": 0, "msg": "success", "data": item.model_dump()}


@router.post("/{automation_id}/pause", response_model=dict)
async def pause_automation(automation_id: str, current_user: User = Depends(get_current_user)):
    item = _store.get(automation_id)
    if not item or item.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Automation not found")
    item.status = AutomationStatus.PAUSED
    _store[automation_id] = item
    return {"code": 0, "msg": "success", "data": item.model_dump()}


@router.post("/{automation_id}/resume", response_model=dict)
async def resume_automation(automation_id: str, current_user: User = Depends(get_current_user)):
    item = _store.get(automation_id)
    if not item or item.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Automation not found")
    item.status = AutomationStatus.ACTIVE
    _store[automation_id] = item
    return {"code": 0, "msg": "success", "data": item.model_dump()}


@router.delete("/{automation_id}", response_model=dict)
async def delete_automation(automation_id: str, current_user: User = Depends(get_current_user)):
    item = _store.get(automation_id)
    if not item or item.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Automation not found")
    del _store[automation_id]
    return {"code": 0, "msg": "success", "data": None}
