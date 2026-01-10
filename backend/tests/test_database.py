from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.core.db import Base
from backend.models.goal import Goal
from backend.models.milestone import Milestone
from backend.models.task import Task

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db_session():
    """
    Pytest fixture to create a new database session for each test function.
    This ensures tests are isolated from each other.
    """
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)  # Create tables
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)  # Drop tables after test

def test_create_goal(db_session):
    """
    Test creating and retrieving a Goal.
    """
    goal = Goal(
        memory_id="test-goal-1",
        title="Test Goal",
        type="Testing",
        deadline=date(2026, 12, 31)
    )
    db_session.add(goal)
    db_session.commit()
    db_session.refresh(goal)

    retrieved_goal = db_session.query(Goal).filter(Goal.id == goal.id).first()
    assert retrieved_goal is not None
    assert retrieved_goal.title == "Test Goal"
    assert retrieved_goal.memory_id == "test-goal-1"

def test_create_milestone_and_relationship(db_session):
    """
    Test creating a Milestone and its relationship with a Goal.
    """
    goal = Goal(
        memory_id="test-goal-2",
        title="Goal for Milestone",
        type="Testing",
        deadline=date(2026, 12, 31)
    )
    milestone = Milestone(
        goal=goal,
        title="Test Milestone",
        target_date=date(2026, 6, 30),
        definition_of_done="Complete testing",
        order=1
    )
    db_session.add(goal)
    db_session.add(milestone)
    db_session.commit()

    retrieved_milestone = db_session.query(Milestone).first()
    assert retrieved_milestone is not None
    assert retrieved_milestone.title == "Test Milestone"
    # Test the relationship
    assert retrieved_milestone.goal.title == "Goal for Milestone"
    assert len(goal.milestones) == 1
    assert goal.milestones[0].title == "Test Milestone"

def test_cascade_delete(db_session):
    """
    Test that deleting a Goal also deletes its child Milestones and Tasks.
    """
    goal = Goal(
        memory_id="test-goal-3",
        title="Goal to be Deleted",
        type="Testing",
        deadline=date(2026, 12, 31)
    )
    milestone = Milestone(goal=goal, title="M1", target_date=date(2026, 1, 1), definition_of_done="dod", order=1)
    task = Task(goal=goal, milestone=milestone, title="T1", due_date=date(2026, 1, 1))
    
    db_session.add_all([goal, milestone, task])
    db_session.commit()

    assert db_session.query(Goal).count() == 1
    assert db_session.query(Milestone).count() == 1
    assert db_session.query(Task).count() == 1

    # Delete the parent goal
    db_session.delete(goal)
    db_session.commit()

    # Assert that children are also deleted
    assert db_session.query(Goal).count() == 0
    assert db_session.query(Milestone).count() == 0
    assert db_session.query(Task).count() == 0
