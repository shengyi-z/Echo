"""
Chat API - Handle user messages and communicate with Backboard AI
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sys
import os

# 添加父目录到路径以便导入 init_echo
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from init_echo import ensure_assistant, create_thread, send_message

router = APIRouter(prefix="/api/chat", tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    thread_id: str = None

class ChatResponse(BaseModel):
    content: str
    thread_id: str
    role: str = "assistant"

class InitRequest(BaseModel):
    user_id: str = None  # 预留给未来的用户系统

class InitResponse(BaseModel):
    assistant_id: str
    thread_id: str
    message: str

@router.post("/init", response_model=InitResponse)
async def initialize_user():
    """
    用户登录时调用：确保助手存在 + 创建新对话线程
    """
    try:
        # 1. 确保助手已创建
        assistant_id = await ensure_assistant()
        
        # 2. 为用户创建新线程
        thread_id = create_thread(assistant_id)
        
        return InitResponse(
            assistant_id=assistant_id,
            thread_id=thread_id,
            message="✅ 初始化成功，可以开始对话了！"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"初始化失败: {e}")

@router.post("/send", response_model=ChatResponse)
async def send_chat_message(request: ChatRequest):
    """
    发送用户消息到 Backboard AI 并返回回复
    """
    if not request.thread_id:
        raise HTTPException(
            status_code=400, 
            detail="请先调用 /api/chat/init 初始化对话"
        )
    
    try:
        # 发送消息，自动开启记忆和搜索
        content = send_message(request.thread_id, request.message)
        
        return ChatResponse(
            content=content,
            thread_id=request.thread_id,
            role="assistant"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发送消息失败: {e}")