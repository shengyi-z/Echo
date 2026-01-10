from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.schemas import ChatRequest, ChatResponse
from app.services.llm_client import llm

router = APIRouter()

@router.post("/", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    response = llm.understand(payload.user_id, payload.message)
    return ChatResponse(message=response)
