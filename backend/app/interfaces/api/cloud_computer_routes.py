"""Cloud Computer routes — Manus Cloud Computer replica.

Persistent sandbox that stays alive beyond a single task, for hosting bots,
servers, and automations. See https://manus.im/features/cloud-computer

Endpoints: /api/v1/cloud-computers
"""

from fastapi import APIRouter, Depends, HTTPException

from app.interfaces.dependencies import get_current_user
from app.domain.models.user import User
from app.domain.models.cloud_computer import CloudComputer, CloudComputerStatus

router = APIRouter(prefix="/cloud-computers", tags=["cloud-computers"])

_store: dict[str, CloudComputer] = {}


@router.get("", response_model=dict)
async def list_cloud_computers(current_user: User = Depends(get_current_user)):
    items = [c for c in _store.values() if c.user_id == current_user.id]
    return {"code": 0, "msg": "success", "data": [c.model_dump() for c in items]}


@router.post("", response_model=dict)
async def create_cloud_computer(
    name: str = "Landis Cloud",
    provider: str = "docker",
    current_user: User = Depends(get_current_user),
):
    cc = CloudComputer(user_id=current_user.id, name=name, sandbox_provider=provider, status=CloudComputerStatus.RUNNING)
    _store[cc.id] = cc
    return {"code": 0, "msg": "success", "data": cc.model_dump()}


@router.get("/{computer_id}", response_model=dict)
async def get_cloud_computer(computer_id: str, current_user: User = Depends(get_current_user)):
    item = _store.get(computer_id)
    if not item or item.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Cloud computer not found")
    return {"code": 0, "msg": "success", "data": item.model_dump()}


@router.post("/{computer_id}/stop", response_model=dict)
async def stop_cloud_computer(computer_id: str, current_user: User = Depends(get_current_user)):
    item = _store.get(computer_id)
    if not item or item.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Cloud computer not found")
    item.status = CloudComputerStatus.STOPPED
    _store[computer_id] = item
    return {"code": 0, "msg": "success", "data": item.model_dump()}


@router.delete("/{computer_id}", response_model=dict)
async def delete_cloud_computer(computer_id: str, current_user: User = Depends(get_current_user)):
    item = _store.get(computer_id)
    if not item or item.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Cloud computer not found")
    del _store[computer_id]
    return {"code": 0, "msg": "success", "data": None}
