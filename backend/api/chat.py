"""
Chat API - Handle user messages and communicate with Backboard AI
"""
import os
from typing import Optional

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..init_echo import ensure_assistant, create_thread, send_message

# Router config and Backboard base URL.
router = APIRouter(prefix="/api/chat", tags=["chat"])
BASE_URL = "https://app.backboard.io/api"

# Request payload for sending a user message.


class ChatRequest(BaseModel):
    message: str
    thread_id: str
    is_first_message: Optional[bool] = False

# Response payload for a chat reply.


class ChatResponse(BaseModel):
    content: str
    thread_id: str
    role: str = "assistant"
    suggested_title: Optional[str] = None

# Response payload for init endpoint.


class InitResponse(BaseModel):
    assistant_id: str
    thread_id: str
    message: str

# Request payload for creating a new chat.


class NewChatRequest(BaseModel):
    title: Optional[str] = None

# Response payload for new chat creation.


class NewChatResponse(BaseModel):
    thread_id: str
    title: str
    created_at: str

# Request payload for updating chat titles.


class UpdateTitleRequest(BaseModel):
    thread_id: str
    title: str

# Response payload for updating chat titles.


class UpdateTitleResponse(BaseModel):
    success: bool
    thread_id: str
    title: str

# Ensure assistant exists and create a new thread.


@router.post("/init", response_model=InitResponse)
async def initialize_user():
    """
    用户登录时调用：确保助手存在 + 创建新对话线程
    """
    try:
        assistant_id = await ensure_assistant()
        thread_id = create_thread(assistant_id)

        return InitResponse(
            assistant_id=assistant_id,
            thread_id=thread_id,
            message="✅ 初始化成功，可以开始对话了！"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"初始化失败: {str(e)}")

# Create a new chat thread.


@router.post("/new", response_model=NewChatResponse)
async def create_new_chat(request: NewChatRequest):
    """
    创建新的对话线程
    """
    try:
        assistant_id = await ensure_assistant()
        thread_id = create_thread(assistant_id)

        from datetime import datetime

        title = request.title if request.title else "New Chat"

        return NewChatResponse(
            thread_id=thread_id,
            title=title,
            created_at=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建新对话失败: {str(e)}")

# Send user message and return AI reply.


@router.post("/send", response_model=ChatResponse)
async def send_chat_message(request: ChatRequest):
    """
    发送用户消息到 Backboard AI 并返回回复
    如果是第一条消息，会根据内容生成建议的标题
    """
    if not request.thread_id:
        raise HTTPException(
            status_code=400,
            detail="请先调用 /api/chat/init 初始化对话"
        )

    try:
        # 发送消息，自动开启记忆和搜索
        print(f"📤 发送消息到 thread_id: {request.thread_id}")
        print(f"📝 消息内容: {request.message}")
        content = send_message(request.thread_id, request.message)
        print(f"✅ 收到回复: {content[:100] if content else 'None'}...")

        suggested_title = None

        # 如果是第一条消息，使用 AI 生成标题
        if request.is_first_message:
            suggested_title = await generate_chat_title_with_ai(request.message)

        return ChatResponse(
            content=content,
            thread_id=request.thread_id,
            role="assistant",
            suggested_title=suggested_title
        )
    except Exception as e:
        print(f"❌ 错误详情: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"发送消息失败: {str(e)}")

# Update stored chat title (frontend-only for now).


@router.post("/update-title", response_model=UpdateTitleResponse)
async def update_chat_title(request: UpdateTitleRequest):
    """
    更新对话标题
    """
    try:
        return UpdateTitleResponse(
            success=True,
            thread_id=request.thread_id,
            title=request.title
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新标题失败: {str(e)}")

# Use AI to generate a short title from the first user message.


async def generate_chat_title_with_ai(user_message: str) -> str:
    """
    使用 AI 根据用户第一条消息生成简短的对话标题
    """
    try:
        api_key = os.getenv("BACKBOARD_API_KEY")
        assistant_id = os.getenv("BACKBOARD_ASSISTANT_ID")

        if not api_key or not assistant_id:
            return generate_simple_title(user_message)

        # 创建临时线程用于生成标题
        headers = {"X-API-Key": api_key}
        response = requests.post(
            f"{BASE_URL}/assistants/{assistant_id}/threads",
            json={},
            headers=headers
        )
        response.raise_for_status()
        temp_thread_id = response.json()["thread_id"]

        # 请求 AI 生成标题
        prompt = f"""Based on this user message, generate a short, descriptive chat title (3-5 words max, no quotes):

User message: "{user_message}"

Reply with ONLY the title, nothing else."""

        payload = {
            "content": prompt,
            "memory": "Off",
            "web_search": "Off",
            "stream": "false"
        }

        response = requests.post(
            f"{BASE_URL}/threads/{temp_thread_id}/messages",
            data=payload,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()

        title = response.json().get("content", "").strip()

        # 清理标题（移除引号等）
        title = title.replace('"', '').replace("'", '').strip()

        # 如果标题太长或为空，使用简单方法
        if len(title) > 40 or len(title) < 3:
            return generate_simple_title(user_message)

        return title

    except Exception as e:
        print(f"AI title generation failed: {e}")
        return generate_simple_title(user_message)

# Fallback: simple title generation when AI fails.


def generate_simple_title(user_message: str) -> str:
    """
    备用方案：简单的标题生成
    """
    words = user_message.split()[:5]
    title = ' '.join(words)
    if len(title) > 30:
        title = title[:27] + "..."
    return title if title else "New Chat"
