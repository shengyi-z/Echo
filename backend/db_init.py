from datetime import date, timedelta

#  use relative import paths
from .core.db import Base, engine, SessionLocal
from .models.goal import Goal
from .models.milestone import Milestone
from .models.task import Task
from .models.dependency import Dependency


def init_db():
    """
    Initializes the database by creating tables and seeding initial data.
    """
    print("Creating database tables...")
    # This command creates all the tables defined by your models
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

    # A database session is the main interface for database interactions
    db = SessionLocal()

    try:
        # Check if there's already data to avoid re-populating
        if db.query(Goal).first():
            print("Database already contains data. Skipping seeding.")
            return

        print("Seeding database with initial data...")

        # 1. Create a Goal instance
        learn_french_goal = Goal(
            title="Learn French to B2 Level",
            memory_id="goal-001",
            type="Language Learning",
            deadline=date.today() + timedelta(days=365),
            budget=500.00,
            weekly_hours=10,
            status="in-progress"
        )

        # 2. Create a Milestone instance for that Goal
        milestone_a1 = Milestone(
            goal=learn_french_goal,  # Associate with the goal
            title="Complete A1 Level",
            target_date=date.today() + timedelta(days=90),
            definition_of_done="Pass the official DELF A1 exam.",
            order=1,
            status="in-progress"
        )

        # 3. Create Task instances for that Milestone
        task_1 = Task(
            goal=learn_french_goal,      # Also link task to the main goal
            milestone=milestone_a1,  # Associate with the milestone
            title="Finish Chapter 1 of grammar book",
            due_date=date.today() + timedelta(days=7),
            priority="high",
            estimated_time=5.0
        )

        task_2 = Task(
            goal=learn_french_goal,
            milestone=milestone_a1,
            title="Have a 15-minute conversation with a language partner",
            due_date=date.today() + timedelta(days=10),
            priority="medium",
            estimated_time=1.5
        )

        # 4. Add the objects to the session
        # SQLAlchemy is smart enough to handle the relationships.
        # Adding the parent object (goal) can be enough if cascade is set up correctly,
        # but adding all is explicit and clear.
        db.add(learn_french_goal)
        db.add(milestone_a1)
        db.add(task_1)
        db.add(task_2)

        # 5. Commit the session to write changes to the database
        db.commit()

        print("Initial data has been seeded successfully.")

    finally:
        # 6. Always close the session
        db.close()


if __name__ == "__main__":
    init_db()
