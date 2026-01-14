from fastapi import APIRouter, HTTPException

from core.db import SessionLocal
from schemas.plan import PlanRequest, PlanResponse
from services.planning_service import PlanningService

# Router configuration for planning endpoints.
router = APIRouter(prefix="/api/plans", tags=["plans"])


# Generate a plan and persist it to the database.
@router.post("/generate", response_model=PlanResponse)
def generate_plan(request: PlanRequest) -> PlanResponse:
    # Create a short-lived DB session per request.
    session = SessionLocal()
    try:
        service = PlanningService(session)
        return service.generate_and_store(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        # Always close the session to avoid connection leaks.
        session.close()
