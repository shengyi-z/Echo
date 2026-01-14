from datetime import date
from typing import List, Mapping, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.db import get_db
from models.dependency import Dependency
from models.task import Task
from repo.task_repo import TaskRepository
from schemas.task import (
    DependencyCreate,
    DependencyOut,
    TaskCreate,
    TaskOut,
    TaskUpdate,
)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def _model_dump(model) -> Mapping[str, object]:
    return model.model_dump() if hasattr(model, "model_dump") else model.dict()


# Create a new task.
@router.post("", response_model=TaskOut)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)) -> TaskOut:
    repo = TaskRepository(db)
    task = repo.create_task(
        goal_id=payload.goal_id,
        milestone_id=payload.milestone_id,
        title=payload.title,
        due_date=payload.due_date,
        priority=payload.priority.value,
        status=payload.status.value,
        estimated_time=payload.estimated_time,
    )
    db.commit()
    return task


# List tasks with optional filters.
@router.get("", response_model=List[TaskOut])
def list_tasks(
    goal_id: Optional[UUID] = None,
    milestone_id: Optional[UUID] = None,
    status: Optional[str] = None,
    due_before: Optional[date] = None,
    due_after: Optional[date] = None,
    order_by: Optional[str] = None,
    order_dir: str = "asc",
    include_relations: bool = False,
    outstanding_only: bool = False,
    db: Session = Depends(get_db),
) -> List[TaskOut]:
    repo = TaskRepository(db)
    return repo.list_tasks(
        goal_id=goal_id,
        milestone_id=milestone_id,
        status=status,
        due_before=due_before,
        due_after=due_after,
        order_by=order_by,
        order_dir=order_dir,
        include_relations=include_relations,
        outstanding_only=outstanding_only,
    )


# Fetch a task by ID.
@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: UUID, db: Session = Depends(get_db)) -> TaskOut:
    repo = TaskRepository(db)
    task = repo.get_task(task_id, include_relations=True)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    return task


# Update a task with partial fields.
@router.patch("/{task_id}", response_model=TaskOut)
def update_task(task_id: UUID, payload: TaskUpdate, db: Session = Depends(get_db)) -> TaskOut:
    repo = TaskRepository(db)
    updates = _model_dump(payload)
    updates = {key: value for key, value in updates.items() if value is not None}

    if "priority" in updates and hasattr(updates["priority"], "value"):
        updates["priority"] = updates["priority"].value
    if "status" in updates and hasattr(updates["status"], "value"):
        updates["status"] = updates["status"].value

    task = repo.update_task(task_id, updates)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    db.commit()
    return task


# Delete a task.
@router.delete("/{task_id}")
def delete_task(task_id: UUID, db: Session = Depends(get_db)) -> Mapping[str, bool]:
    repo = TaskRepository(db)
    deleted = repo.delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found.")
    db.commit()
    return {"success": True}


# Create a dependency between two tasks.
@router.post("/dependencies", response_model=DependencyOut)
def create_dependency(payload: DependencyCreate, db: Session = Depends(get_db)) -> DependencyOut:
    if payload.from_task_id == payload.to_task_id:
        raise HTTPException(status_code=400, detail="A task cannot depend on itself.")

    from_task = db.get(Task, payload.from_task_id)
    to_task = db.get(Task, payload.to_task_id)
    if not from_task or not to_task:
        raise HTTPException(status_code=404, detail="Task not found.")

    exists = (
        db.query(Dependency)
        .filter(
            Dependency.from_task_id == payload.from_task_id,
            Dependency.to_task_id == payload.to_task_id,
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=409, detail="Dependency already exists.")

    dependency = Dependency(
        from_task_id=payload.from_task_id,
        to_task_id=payload.to_task_id,
    )
    db.add(dependency)
    db.commit()
    db.refresh(dependency)
    return dependency


# List dependencies for a task (incoming/outgoing).
@router.get("/{task_id}/dependencies", response_model=List[DependencyOut])
def list_dependencies(task_id: UUID, db: Session = Depends(get_db)) -> List[DependencyOut]:
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    return list(
        db.query(Dependency)
        .filter(
            (Dependency.from_task_id == task_id) | (Dependency.to_task_id == task_id)
        )
        .all()
    )


# Delete a dependency by ID.
@router.delete("/dependencies/{dependency_id}")
def delete_dependency(
    dependency_id: UUID,
    db: Session = Depends(get_db),
) -> Mapping[str, bool]:
    dependency = db.get(Dependency, dependency_id)
    if not dependency:
        raise HTTPException(status_code=404, detail="Dependency not found.")
    db.delete(dependency)
    db.commit()
    return {"success": True}
