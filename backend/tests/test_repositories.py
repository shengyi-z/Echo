from datetime import date, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.core.db import Base
from backend.repo.goal_repo import GoalRepository
from backend.repo.task_repo import TaskRepository


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def _create_goal_with_milestone(session):
    goal_repo = GoalRepository(session)
    goal = goal_repo.create_goal(
        memory_id="memory-1",
        title="Plan a move to Montreal",
        type="relocation",
        deadline=date.today() + timedelta(days=90),
        milestones=[
            {
                "title": "Visa preparation",
                "target_date": date.today() + timedelta(days=30),
                "definition_of_done": "Application submitted",
                "tasks": [
                    {
                        "title": "Collect recommendation letters",
                        "due_date": date.today() + timedelta(days=10),
                    },
                    {
                        "title": "Schedule biometrics appointment",
                        "due_date": date.today() + timedelta(days=15),
                        "priority": "high",
                    },
                ],
            }
        ],
    )
    session.flush()
    return goal


def test_goal_repository_creates_related_rows(session):
    goal = _create_goal_with_milestone(session)

    assert goal.id is not None
    assert len(goal.milestones) == 1
    milestone = goal.milestones[0]
    assert milestone.tasks  # tasks were created via payload
    assert milestone.tasks[0].goal_id == goal.id


def test_goal_progress_snapshot_counts_children(session):
    goal = _create_goal_with_milestone(session)
    snapshot = GoalRepository(session).get_progress_snapshot(goal.id)

    assert snapshot is not None
    assert snapshot["milestones"]["total"] == 1
    assert snapshot["tasks"]["total"] == 2
    assert snapshot["tasks"]["percent_complete"] == 0.0


def test_task_repository_due_filters(session):
    goal = _create_goal_with_milestone(session)
    milestone = goal.milestones[0]
    repo = TaskRepository(session)

    # Add one overdue and one upcoming task.
    repo.create_task(
        goal_id=goal.id,
        milestone_id=milestone.id,
        title="Book moving company",
        due_date=date.today() - timedelta(days=2),
    )
    repo.create_task(
        goal_id=goal.id,
        milestone_id=milestone.id,
        title="Find housing options",
        due_date=date.today() + timedelta(days=2),
    )

    overdue = repo.get_overdue_tasks()
    assert any(task.title == "Book moving company" for task in overdue)

    due_soon = repo.get_due_tasks(window_days=3)
    assert any(task.title == "Find housing options" for task in due_soon)
