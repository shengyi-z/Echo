from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import date

from ..core.db import SessionLocal, get_db
from ..schemas.plan import PlanRequest, PlanResponse
from ..services.planning_service import PlanningService
from ..repo.goal_repo import GoalRepository
from ..schemas.goal import GoalType

# Router configuration for planning endpoints.
router = APIRouter(prefix="/api/plans", tags=["plans"])


# Generate a plan and persist it to the database.
@router.post("/generate", response_model=PlanResponse)
async def generate_plan(request: PlanRequest) -> PlanResponse:
    # Create a short-lived DB session per request.
    session = SessionLocal()
    try:
        service = PlanningService(session)
        return await service.generate_and_store(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        # Always close the session to avoid connection leaks.
        session.close()


# Schema for confirming a plan
class ConfirmPlanMilestone(BaseModel):
    id: str
    title: str
    target_date: date
    definition_of_done: str
    order: int


class ConfirmPlanRequest(BaseModel):
    thread_id: str
    goal_title: str
    goal_type: str  # Will be mapped to GoalType
    deadline: date
    milestones: List[ConfirmPlanMilestone]
    response_to_user: Optional[str] = None


class ConfirmPlanResponse(BaseModel):
    success: bool
    message: str
    goal_id: Optional[str] = None


# Confirm and save plan to database as Goal with Milestones
@router.post("/confirm", response_model=ConfirmPlanResponse)
async def confirm_plan(
    request: ConfirmPlanRequest,
    db: Session = Depends(get_db)
) -> ConfirmPlanResponse:
    """
    Convert a tentative plan to a confirmed Goal with Milestones in the database.
    
    Args:
        request: Plan data from frontend (milestones, deadline, etc.)
        db: Database session
    
    Returns:
        Success status and goal_id
    """
    try:
        repo = GoalRepository(db)
        
        # Map goal_type string to GoalType enum
        goal_type_map = {
            'visa': GoalType.VISA,
            'language': GoalType.LANGUAGE,
            'fitness': GoalType.FITNESS,
            'study': GoalType.STUDY,
            'career': GoalType.CAREER,
            'finance': GoalType.FINANCE,
            'health': GoalType.HEALTH,
            'travel': GoalType.TRAVEL,
            'other': GoalType.OTHER
        }
        
        goal_type_enum = goal_type_map.get(
            request.goal_type.lower(), 
            GoalType.OTHER
        )
        
        # Prepare milestones data
        milestones_data = []
        for milestone in request.milestones:
            milestones_data.append({
                'title': milestone.title,
                'target_date': milestone.target_date,
                'definition_of_done': milestone.definition_of_done,
                'order': milestone.order,
                'tasks': []  # Tasks will be added later when user breaks down milestones
            })
        
        # Create goal with milestones
        goal = repo.create_goal(
            memory_id=request.thread_id,  # Use thread_id as memory_id
            title=request.goal_title,
            type=goal_type_enum.value,
            deadline=request.deadline,
            status='not-started',
            milestones=milestones_data
        )
        
        db.commit()
        
        return ConfirmPlanResponse(
            success=True,
            message=f"Goal '{request.goal_title}' created successfully with {len(milestones_data)} milestones",
            goal_id=str(goal.id)
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to confirm plan: {str(e)}"
        ) from e
