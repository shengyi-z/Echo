from datetime import date
from typing import List, Mapping, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload

from ..core.db import get_db
from ..models.milestone import Milestone
from ..repo.goal_repo import GoalRepository
from ..schemas.goal import (
    GoalCreate,
    GoalOut,
    GoalUpdate,
    MilestoneCreate,
    MilestoneOut,
    MilestoneUpdate,
)

router = APIRouter(prefix="/api/goals", tags=["goals"])


def _model_dump(model) -> Mapping[str, object]:
    return model.model_dump() if hasattr(model, "model_dump") else model.dict()

def _normalize_enum(value):
    return value.value if hasattr(value, "value") else value


# Create a goal and optional milestone/task hierarchy.
@router.post("", response_model=GoalOut)
def create_goal(payload: GoalCreate, db: Session = Depends(get_db)) -> GoalOut:
    repo = GoalRepository(db)
    existing_goal = repo.get_goal_by_memory_id(payload.memory_id)
    if existing_goal:
        raise HTTPException(
            status_code=409,
            detail="Goal with this memory_id already exists.",
        )
    milestones_payload = []
    for milestone in payload.milestones:
        milestone_data = _model_dump(milestone)
        milestone_data["status"] = _normalize_enum(milestone_data.get("status"))
        tasks_payload = []
        for task in milestone.tasks:
            task_data = _model_dump(task)
            task_data["priority"] = _normalize_enum(task_data.get("priority"))
            task_data["status"] = _normalize_enum(task_data.get("status"))
            tasks_payload.append(task_data)
        milestone_data["tasks"] = tasks_payload
        milestones_payload.append(milestone_data)

    goal = repo.create_goal(
        memory_id=payload.memory_id,
        title=payload.title,
        type=payload.type.value,
        deadline=payload.deadline,
        budget=payload.budget,
        weekly_hours=payload.weekly_hours,
        status=payload.status.value,
        milestones=milestones_payload,
    )
    db.commit()

    stored_goal = repo.get_goal(goal.id, include_children=True)
    if not stored_goal:
        raise HTTPException(status_code=500, detail="Failed to load created goal.")
    return stored_goal


# List goals with optional filters.
@router.get("", response_model=List[GoalOut])
def list_goals(
    status: Optional[str] = None,
    type: Optional[str] = Query(default=None, alias="type"),
    due_before: Optional[date] = None,
    include_children: bool = False,
    db: Session = Depends(get_db),
) -> List[GoalOut]:
    repo = GoalRepository(db)
    return repo.list_goals(
        status=status,
        type_=type,
        due_before=due_before,
        include_children=include_children,
    )


# Fetch a single goal by ID.
@router.get("/{goal_id}", response_model=GoalOut)
def get_goal(
    goal_id: UUID,
    include_children: bool = True,
    db: Session = Depends(get_db),
) -> GoalOut:
    repo = GoalRepository(db)
    goal = repo.get_goal(goal_id, include_children=include_children)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found.")
    return goal


# Update a goal with partial fields.
@router.patch("/{goal_id}", response_model=GoalOut)
def update_goal(
    goal_id: UUID,
    payload: GoalUpdate,
    db: Session = Depends(get_db),
) -> GoalOut:
    repo = GoalRepository(db)
    updates = _model_dump(payload)
    updates = {key: value for key, value in updates.items() if value is not None}

    if "type" in updates and hasattr(updates["type"], "value"):
        updates["type"] = updates["type"].value
    if "status" in updates and hasattr(updates["status"], "value"):
        updates["status"] = updates["status"].value

    goal = repo.update_goal(goal_id, updates)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found.")
    db.commit()

    stored_goal = repo.get_goal(goal_id, include_children=True)
    if not stored_goal:
        raise HTTPException(status_code=500, detail="Failed to load updated goal.")
    return stored_goal


# Delete a goal and its related milestones/tasks.
@router.delete("/{goal_id}")
def delete_goal(goal_id: UUID, db: Session = Depends(get_db)) -> Mapping[str, bool]:
    repo = GoalRepository(db)
    deleted = repo.delete_goal(goal_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Goal not found.")
    db.commit()
    return {"success": True}


# Create a milestone under a specific goal.
@router.post("/{goal_id}/milestones", response_model=MilestoneOut)
def create_milestone(
    goal_id: UUID,
    payload: MilestoneCreate,
    db: Session = Depends(get_db),
) -> MilestoneOut:
    repo = GoalRepository(db)
    tasks_payload = []
    for task in payload.tasks:
        task_data = _model_dump(task)
        task_data["priority"] = _normalize_enum(task_data.get("priority"))
        task_data["status"] = _normalize_enum(task_data.get("status"))
        tasks_payload.append(task_data)
    milestone = repo.add_milestone(
        goal_id,
        title=payload.title,
        target_date=payload.target_date,
        definition_of_done=payload.definition_of_done,
        order=payload.order,
        status=payload.status.value,
        tasks=tasks_payload,
    )
    db.commit()
    return milestone


# List milestones for a specific goal.
@router.get("/{goal_id}/milestones", response_model=List[MilestoneOut])
def list_goal_milestones(
    goal_id: UUID,
    include_tasks: bool = True,
    db: Session = Depends(get_db),
) -> List[MilestoneOut]:
    query = db.query(Milestone).where(Milestone.goal_id == goal_id)
    if include_tasks:
        query = query.options(selectinload(Milestone.tasks))
    return list(query.order_by(Milestone.order.asc()).all())


# Update a milestone for a specific goal.
@router.patch("/{goal_id}/milestones/{milestone_id}", response_model=MilestoneOut)
def update_goal_milestone(
    goal_id: UUID,
    milestone_id: UUID,
    payload: MilestoneUpdate,
    db: Session = Depends(get_db),
) -> MilestoneOut:
    milestone = db.get(Milestone, milestone_id)
    if not milestone or milestone.goal_id != goal_id:
        raise HTTPException(status_code=404, detail="Milestone not found.")

    updates = _model_dump(payload)
    updates = {key: value for key, value in updates.items() if value is not None}
    if "status" in updates:
        updates["status"] = updates["status"].value

    for field, value in updates.items():
        setattr(milestone, field, value)

    db.commit()
    db.refresh(milestone)
    return milestone


# Delete a milestone and its tasks.
@router.delete("/{goal_id}/milestones/{milestone_id}")
def delete_goal_milestone(
    goal_id: UUID,
    milestone_id: UUID,
    db: Session = Depends(get_db),
) -> Mapping[str, bool]:
    milestone = db.get(Milestone, milestone_id)
    if not milestone or milestone.goal_id != goal_id:
        raise HTTPException(status_code=404, detail="Milestone not found.")
    db.delete(milestone)
    db.commit()
    return {"success": True}
