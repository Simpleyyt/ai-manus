"""Automations — scheduled and event-triggered tasks.

Manus 2.0 Automations docs: https://manus.im/docs/automations
Three patterns:
  1. Schedule — cron/timer (e.g. daily report)
  2. Triggered task — reacts to event (new email, PR, calendar)
  3. Advanced — multi-source + conditions + actions

In the replica, automations are stored as domain models and executed via
Celery beat (when TASK_BACKEND=celery) or via asyncio loop (TASK_BACKEND=local).

See also frontend: automations panel should list/crud these.
"""

from datetime import datetime, UTC
from enum import Enum
from typing import Optional, Any

from pydantic import BaseModel, Field
import uuid


class AutomationTriggerType(str, Enum):
    SCHEDULE = "schedule"  # cron/interval
    EVENT = "event"  # webhook / external event
    ADVANCED = "advanced"  # conditions + actions


class AutomationStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    ERROR = "error"


class AutomationSchedule(BaseModel):
    """Schedule config for SCHEDULE trigger."""

    cron: Optional[str] = None  # e.g. "0 9 * * 1" (Manus cron)
    interval_minutes: Optional[int] = None
    timezone: str = "UTC"


class Automation(BaseModel):
    """Automation definition."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    user_id: str
    project_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    trigger_type: AutomationTriggerType = AutomationTriggerType.SCHEDULE
    schedule: Optional[AutomationSchedule] = None
    # For EVENT/ADVANCED: webhook source, conditions, actions
    source: Optional[str] = None  # e.g. gmail, github, slack, notion, calendar
    conditions: dict = Field(default_factory=dict)
    actions: dict = Field(default_factory=dict)
    # Execution: what task to run
    task_prompt: str = ""  # the agent prompt to execute
    skill: Optional[str] = None  # optional skill to invoke
    status: AutomationStatus = AutomationStatus.ACTIVE
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    run_count: int = 0
    error_message: Optional[str] = None

    model_config = {"use_enum_values": False}


class AutomationRun(BaseModel):
    """A single execution of an automation."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    automation_id: str
    session_id: Optional[str] = None  # linked session
    status: str = "pending"  # pending | running | completed | failed
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    finished_at: Optional[datetime] = None
    result: Optional[str] = None
    error: Optional[str] = None
