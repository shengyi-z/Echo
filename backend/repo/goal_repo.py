from __future__ import annotations

from datetime import date, timedelta
from typing import Mapping, MutableMapping, Optional, Sequence
from uuid import UUID

from sqlalchemy import Select, case, func, select
from sqlalchemy.orm import Session, selectinload

from ..models.goal import Goal
from ..models.milestone import Milestone
from ..models.task import Task


class GoalRepository:
    """
    Data-access layer for long-term planning goals.

    The repository encapsulates the CRUD logic for goals, milestones, and the
    derived progress metrics that power the assistant.  Business services can
    depend on this class to ensure consistent behavior regardless of whether
    the caller is a FastAPI endpoint, an automation job, or a background
    reminder worker.
    """

    def __init__(self, session: Session):
        self.session = session

    # --------------------------------------------------------------------- #
    # Goal CRUD helpers
    # --------------------------------------------------------------------- #
    def create_goal(
        self,
        *,
        memory_id: str,
        title: str,
        type: str,
        deadline: date,
        budget: Optional[float] = None,
        weekly_hours: Optional[int] = None,
        status: str = "not-started",
        milestones: Optional[Sequence[Mapping[str, object]]] = None,
    ) -> Goal:
        """
        Persist a new goal and optional milestone/task hierarchy.

        The milestones payload accepts dictionaries with the following keys:
        - title (str)
        - target_date (date)
        - definition_of_done (str)
        - order (int, optional)
        - status (str, optional)
        - tasks (Sequence[Mapping]) - optional task definitions
        """
        goal = Goal(
            memory_id=memory_id,
            title=title,
            type=type,
            deadline=deadline,
            budget=budget,
            weekly_hours=weekly_hours,
            status=status,
        )
        self.session.add(goal)
        self.session.flush()  # Ensure the goal has an ID for FK relationships.

        if milestones:
            for idx, milestone_data in enumerate(milestones, start=1):
                self._create_milestone_from_payload(
                    goal,
                    milestone_data,
                    default_order=idx,
                )

        return goal

    def get_goal(
        self,
        goal_id: UUID,
        *,
        include_children: bool = False,
    ) -> Optional[Goal]:
        """
        Load a single goal by ID.  Optionally pre-fetch milestones and tasks.
        """
        statement: Select[Goal] = select(Goal).where(Goal.id == goal_id)
        if include_children:
            statement = statement.options(
                selectinload(Goal.milestones)
                .selectinload(Milestone.tasks),
                selectinload(Goal.tasks),
            )
        return self.session.execute(statement).scalar_one_or_none()

    def get_goal_by_memory_id(self, memory_id: str) -> Optional[Goal]:
        statement = select(Goal).where(Goal.memory_id == memory_id)
        return self.session.execute(statement).scalar_one_or_none()

    def list_goals(
        self,
        *,
        status: Optional[str] = None,
        type_: Optional[str] = None,
        due_before: Optional[date] = None,
        include_children: bool = False,
    ) -> list[Goal]:
        """
        Flexible query for filtering goals by status, type, or deadline.
        """
        statement: Select[Goal] = select(Goal)

        if status:
            statement = statement.where(Goal.status == status)
        if type_:
            statement = statement.where(Goal.type == type_)
        if due_before:
            statement = statement.where(Goal.deadline <= due_before)

        if include_children:
            statement = statement.options(
                selectinload(Goal.milestones)
                .selectinload(Milestone.tasks),
                selectinload(Goal.tasks),
            )

        statement = statement.order_by(Goal.deadline.asc())
        return list(self.session.execute(statement).scalars().all())

    def update_goal(self, goal_id: UUID, updates: Mapping[str, object]) -> Optional[Goal]:
        """
        Apply a set of column updates to a goal.  Only whitelisted attributes
        are mutatable to avoid accidental mass assignment.
        """
        goal = self.session.get(Goal, goal_id)
        if not goal:
            return None

        allowed_fields = {
            "title",
            "type",
            "deadline",
            "budget",
            "weekly_hours",
            "status",
            "memory_id",
        }
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(goal, field, value)

        self.session.flush()
        return goal

    def delete_goal(self, goal_id: UUID) -> bool:
        goal = self.session.get(Goal, goal_id)
        if not goal:
            return False
        self.session.delete(goal)
        return True

    # --------------------------------------------------------------------- #
    # Milestone helpers
    # --------------------------------------------------------------------- #
    def add_milestone(
        self,
        goal_id: UUID,
        *,
        title: str,
        target_date: date,
        definition_of_done: str,
        order: Optional[int] = None,
        status: str = "not-started",
        tasks: Optional[Sequence[Mapping[str, object]]] = None,
    ) -> Milestone:
        goal = self.session.get(Goal, goal_id)
        if not goal:
            raise ValueError(f"Goal {goal_id} does not exist.")

        if order is None:
            order = len(goal.milestones) + 1

        milestone_payload: MutableMapping[str, object] = {
            "title": title,
            "target_date": target_date,
            "definition_of_done": definition_of_done,
            "order": order,
            "status": status,
        }
        if tasks:
            milestone_payload["tasks"] = tasks

        milestone = self._create_milestone_from_payload(
            goal, milestone_payload, default_order=order)
        self.session.flush()
        return milestone

    def reorder_milestones(self, goal_id: UUID, ordered_ids: Sequence[UUID]) -> None:
        """
        Update the execution order for milestones.  Missing IDs are ignored.
        """
        goal = self.session.get(Goal, goal_id)
        if not goal:
            raise ValueError(f"Goal {goal_id} does not exist.")

        index_map = {milestone_id: idx for idx,
                     milestone_id in enumerate(ordered_ids, start=1)}
        for milestone in goal.milestones:
            if milestone.id in index_map:
                milestone.order = index_map[milestone.id]

        self.session.flush()

    # --------------------------------------------------------------------- #
    # Progress insights for reminder/progress services
    # --------------------------------------------------------------------- #
    def get_progress_snapshot(self, goal_id: UUID) -> Optional[dict]:
        """
        Return aggregated counts for milestones/tasks so services can estimate
        overall progress and decide when nudges are necessary.
        """
        goal = self.session.get(Goal, goal_id)
        if not goal:
            return None

        milestone_counts = self.session.execute(
            select(
                func.count(Milestone.id),
                func.sum(case((Milestone.status == "completed", 1), else_=0)),
            ).where(Milestone.goal_id == goal_id)
        ).one()

        task_counts = self.session.execute(
            select(
                func.count(Task.id),
                func.sum(case((Task.status == "completed", 1), else_=0)),
            ).where(Task.goal_id == goal_id)
        ).one()

        total_milestones = milestone_counts[0] or 0
        completed_milestones = milestone_counts[1] or 0
        total_tasks = task_counts[0] or 0
        completed_tasks = task_counts[1] or 0

        def _percentage(done: int, total: int) -> float:
            return round((done / total) * 100, 2) if total else 0.0

        return {
            "goal_id": goal_id,
            "status": goal.status,
            "goal_deadline": goal.deadline,
            "milestones": {
                "total": total_milestones,
                "completed": completed_milestones,
                "percent_complete": _percentage(completed_milestones, total_milestones),
            },
            "tasks": {
                "total": total_tasks,
                "completed": completed_tasks,
                "percent_complete": _percentage(completed_tasks, total_tasks),
            },
        }

    def get_upcoming_deadlines(self, window_days: int = 7) -> list[Goal]:
        """
        Surface goals approaching their deadline so the reminder system can
        nudge the user.  Only goals that are not yet complete are returned.
        """
        today = date.today()
        limit = today + timedelta(days=window_days)

        statement = (
            select(Goal)
            .where(Goal.status != "completed")
            .where(Goal.deadline.between(today, limit))
            .order_by(Goal.deadline.asc())
        )
        return list(self.session.execute(statement).scalars().all())

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #
    def _create_milestone_from_payload(
        self,
        goal: Goal,
        payload: Mapping[str, object],
        *,
        default_order: int,
    ) -> Milestone:
        milestone = Milestone(
            goal=goal,
            title=str(payload["title"]),
            target_date=payload["target_date"],
            definition_of_done=str(payload.get("definition_of_done", "")),
            order=int(payload.get("order", default_order)),
            status=str(payload.get("status") or "not-started"),
        )
        self.session.add(milestone)

        for task_payload in payload.get("tasks", []) or []:
            task = Task(
                goal=goal,
                milestone=milestone,
                title=str(task_payload["title"]),
                due_date=task_payload["due_date"],
                priority=str(task_payload.get("priority") or "medium"),
                status=str(task_payload.get("status") or "not-started"),
                estimated_time=task_payload.get("estimated_time"),
            )
            self.session.add(task)

        return milestone
