from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable, Mapping, Optional, Sequence
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from ..models.goal import Goal
from ..models.milestone import Milestone
from ..models.task import Task


class TaskRepository:
    """
    Data-access layer dedicated to milestone tasks.

    Tasks are the most tactical unit in the long-term planning workflow: they
    map the research, booking, and paperwork required to reach each milestone.
    The repository centralizes the read/write logic so services can focus on
    orchestration and reminders rather than SQLAlchemy boilerplate.
    """

    def __init__(self, session: Session):
        self.session = session

    # ------------------------------------------------------------------ #
    # Task CRUD operations
    # ------------------------------------------------------------------ #
    def create_task(
        self,
        *,
        goal_id: UUID,
        milestone_id: UUID,
        title: str,
        due_date: date,
        priority: str = "medium",
        status: str = "not-started",
        estimated_time: Optional[float] = None,
    ) -> Task:
        milestone = self.session.get(Milestone, milestone_id)
        if not milestone:
            raise ValueError(f"Milestone {milestone_id} does not exist.")
        if milestone.goal_id != goal_id:
            raise ValueError("Milestone does not belong to the supplied goal.")

        task = Task(
            goal_id=goal_id,
            milestone_id=milestone_id,
            title=title,
            due_date=due_date,
            priority=priority,
            status=status,
            estimated_time=estimated_time,
        )

        self.session.add(task)
        self.session.flush()
        return task

    def bulk_create(
        self,
        *,
        goal_id: UUID,
        milestone_id: UUID,
        tasks: Sequence[Mapping[str, object]],
    ) -> list[Task]:
        """
        Convenience helper for adding many tasks during AI-driven breakdowns.
        """
        created: list[Task] = []
        for payload in tasks:
            created.append(
                self.create_task(
                    goal_id=goal_id,
                    milestone_id=milestone_id,
                    title=str(payload["title"]),
                    due_date=payload["due_date"],
                    priority=str(payload.get("priority") or "medium"),
                    status=str(payload.get("status") or "not-started"),
                    estimated_time=payload.get("estimated_time"),
                )
            )
        return created

    def get_task(self, task_id: UUID, include_relations: bool = False) -> Optional[Task]:
        statement: Select[Task] = select(Task).where(Task.id == task_id)
        if include_relations:
            statement = statement.options(
                selectinload(Task.milestone),
                selectinload(Task.goal),
            )
        return self.session.execute(statement).scalar_one_or_none()

    def list_tasks(
        self,
        *,
        goal_id: Optional[UUID] = None,
        milestone_id: Optional[UUID] = None,
        status: Optional[str] = None,
        due_before: Optional[date] = None,
        due_after: Optional[date] = None,
        order_by: Optional[str] = None,
        order_dir: str = "asc",
        include_relations: bool = False,
        outstanding_only: bool = False,
    ) -> list[Task]:
        statement: Select[Task] = select(Task)

        if goal_id:
            statement = statement.where(Task.goal_id == goal_id)
        if milestone_id:
            statement = statement.where(Task.milestone_id == milestone_id)
        if status:
            statement = statement.where(Task.status == status)
        if due_before:
            statement = statement.where(Task.due_date <= due_before)
        if due_after:
            statement = statement.where(Task.due_date >= due_after)
        if outstanding_only:
            statement = statement.where(Task.status != "completed")

        if include_relations:
            statement = statement.options(
                selectinload(Task.milestone),
                selectinload(Task.goal),
            )

        statement = self._apply_sort(statement, order_by=order_by, order_dir=order_dir)
        return list(self.session.execute(statement).scalars().all())

    def update_task(self, task_id: UUID, updates: Mapping[str, object]) -> Optional[Task]:
        task = self.session.get(Task, task_id)
        if not task:
            return None

        allowed_fields = {
            "title",
            "due_date",
            "priority",
            "status",
            "estimated_time",
            "milestone_id",
        }
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(task, field, value)

        self.session.flush()
        return task

    def set_status(self, task_id: UUID, status: str) -> Optional[Task]:
        return self.update_task(task_id, {"status": status})

    def delete_task(self, task_id: UUID) -> bool:
        task = self.session.get(Task, task_id)
        if not task:
            return False
        self.session.delete(task)
        return True

    # ------------------------------------------------------------------ #
    # Scheduling helpers
    # ------------------------------------------------------------------ #
    def get_due_tasks(self, window_days: int = 3) -> list[Task]:
        """
        Return tasks that are due soon so reminder services can ping the user.
        """
        today = date.today()
        upcoming = today + timedelta(days=window_days)
        statement = (
            select(Task)
            .where(Task.status != "completed")
            .where(Task.due_date.between(today, upcoming))
            .order_by(Task.due_date.asc())
        )
        return list(self.session.execute(statement).scalars().all())

    def get_overdue_tasks(self) -> list[Task]:
        """
        Return tasks that slipped past their deadline.
        """
        today = date.today()
        statement = (
            select(Task)
            .where(Task.status != "completed")
            .where(Task.due_date < today)
            .order_by(Task.due_date.asc())
        )
        return list(self.session.execute(statement).scalars().all())

    def attach_tasks_to_goal(self, goal_id: UUID, tasks: Iterable[Task]) -> Goal:
        """
        Helper used by services that synthesize plans externally and now need
        to associate those Task objects with a persisted goal.
        """
        goal = self.session.get(Goal, goal_id)
        if not goal:
            raise ValueError(f"Goal {goal_id} does not exist.")

        for task in tasks:
            task.goal_id = goal_id
            # If a milestone was not assigned we fall back to None and let the
            # caller decide whether to create a general bucket milestone.
            if task.milestone_id is None and goal.milestones:
                task.milestone_id = goal.milestones[0].id

        self.session.flush()
        return goal

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _apply_sort(
        statement: Select[Task],
        *,
        order_by: Optional[str],
        order_dir: str,
    ) -> Select[Task]:
        direction = (order_dir or "asc").lower()
        is_desc = direction == "desc"

        if order_by == "priority":
            column = Task.priority
        elif order_by == "status":
            column = Task.status
        elif order_by == "title":
            column = Task.title
        else:
            column = Task.due_date

        if is_desc:
            return statement.order_by(column.desc())
        return statement.order_by(column.asc())
