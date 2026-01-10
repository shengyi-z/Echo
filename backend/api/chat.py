"""
Chat API - Handle user messages and communicate with Backboard AI
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sys
import os
from typing import List, Optional

# 添加父目录到路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from init_echo import ensure_assistant, create_thread, send_message

router = APIRouter(prefix="/api/chat", tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    thread_id: str

class ChatResponse(BaseModel):
    content: str
    thread_id: str
    role: str = "assistant"

class InitResponse(BaseModel):
    assistant_id: str
    thread_id: str
    message: str

class NewChatRequest(BaseModel):
    title: Optional[str] = "New Chat"

class NewChatResponse(BaseModel):
    thread_id: str
    title: str
    created_at: str

class ChatHistoryItem(BaseModel):
    thread_id: str
    title: str
    preview: str
    created_at: str

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
        raise HTTPException(status_code=500, detail=f"初始化失败: {str(e)}")

@router.post("/new", response_model=NewChatResponse)
async def create_new_chat(request: NewChatRequest):
    """
    创建新的对话线程
    """
    try:
        # 确保助手存在
        assistant_id = await ensure_assistant()
        
        # 创建新线程
        thread_id = create_thread(assistant_id)
        
        from datetime import datetime
        
        return NewChatResponse(
            thread_id=thread_id,
            title=request.title,
            created_at=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建新对话失败: {str(e)}")

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
        raise HTTPException(status_code=500, detail=f"发送消息失败: {str(e)}")