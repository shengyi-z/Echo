from datetime import date, timedelta
from typing import List, Mapping

from sqlalchemy.orm import Session

from ..repo.goal_repo import GoalRepository
from ..schemas.plan import PlanRequest, PlanResponse, PlanMilestone, PlanTask, PlanArtifact


# Planning workflow orchestration for plan generation + persistence.
class PlanningService:
    def __init__(self, session: Session):
        # DB session is injected so callers control lifecycle.
        self.session = session
        self.goal_repo = GoalRepository(session)

    # Public entrypoint: generate a plan and store it in the DB.
    def generate_and_store(self, request: PlanRequest) -> PlanResponse:
        if not request.goal:
            raise ValueError("goal is required to generate a plan")

        # Resolve memory/thread identity for linking to Backboard context.
        memory_id = (
            request.goal.memory_id
            or str(request.current_state.get("memory_id") or "")
            or str(request.current_state.get("thread_id") or "")
        ).strip()
        if not memory_id:
            raise ValueError("memory_id is required to store the plan")

        # Build milestone/task payloads for initial MVP plan.
        milestones_payload = self._build_milestones_payload(request)

        goal = self.goal_repo.create_goal(
            memory_id=memory_id,
            title=request.goal.title,
            type=request.goal.type.value,
            deadline=request.goal.deadline,
            budget=request.goal.budget,
            weekly_hours=request.goal.weekly_hours,
            status="not-started",
            milestones=milestones_payload,
        )
        self.session.commit()
 
        # Reload with children so we can format a full response.
        stored_goal = self.goal_repo.get_goal(goal.id, include_children=True)
        if not stored_goal:
            raise ValueError("failed to load stored plan")

        # Map stored entities into response schemas.
        milestones = [
            PlanMilestone(
                id=str(milestone.id),
                title=milestone.title,
                target_date=milestone.target_date,
                definition_of_done=milestone.definition_of_done,
                order=milestone.order,
            )
            for milestone in stored_goal.milestones
        ]
        tasks = [
            PlanTask(
                id=str(task.id),
                title=task.title,
                due_date=task.due_date,
                milestone_id=str(task.milestone_id),
                priority=task.priority,
                estimated_time=task.estimated_time,
            )
            for task in stored_goal.tasks
        ]

        # Return a structured plan response for the client.
        return PlanResponse(
            date=date.today(),
            focus=stored_goal.title,
            milestones=milestones,
            tasks=tasks,
            artifacts=[],
            message="Plan generated and stored.",
            warnings=[],
        )

    # Build initial milestone/task payloads for an MVP plan.
    def _build_milestones_payload(self, request: PlanRequest) -> List[Mapping[str, object]]:
        today = date.today()
        deadline = request.goal.deadline
        target_date = self._clamp_date(min(deadline, today + timedelta(days=14)), today)

        tasks = self._default_tasks(deadline=deadline, today=today)

        return [
            {
                "title": f"Kickoff: {request.goal.title}",
                "target_date": target_date,
                "definition_of_done": "Initial plan, resources, and schedule are in place.",
                "order": 1,
                "status": "not-started",
                "tasks": tasks,
            }
        ]

    # Default starter tasks before LLM-based planning is added.
    def _default_tasks(self, *, deadline: date, today: date) -> List[Mapping[str, object]]:
        def _due_in(days: int) -> date:
            return self._clamp_date(min(deadline, today + timedelta(days=days)), today)

        return [
            {
                "title": "Define milestones and success criteria",
                "due_date": _due_in(3),
                "priority": "high",
                "estimated_time": 2.0,
            },
            {
                "title": "Collect key resources and links",
                "due_date": _due_in(5),
                "priority": "medium",
                "estimated_time": 1.5,
            },
            {
                "title": "Schedule the first work block",
                "due_date": _due_in(7),
                "priority": "medium",
                "estimated_time": 1.0,
            },
        ]

    # Clamp dates to avoid creating tasks earlier than today.
    @staticmethod
    def _clamp_date(target: date, earliest: date) -> date:
        return target if target >= earliest else earliest
