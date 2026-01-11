import os
import asyncio
from typing import Optional
from backboard import BackboardClient
from dotenv import load_dotenv

load_dotenv()


class ChatService:
    """
    统一的 AI 消息服务，作为所有与 Backboard AI 交互的单一入口。
    """
    
    def __init__(self, api_key: Optional[str] = None, default_thread_id: Optional[str] = None):
        """
        初始化 ChatService。
        
        Args:
            api_key: 可选的 API key，如果不提供则从环境变量读取
            default_thread_id: 可选的默认 thread ID，用于向后兼容
        """
        self.api_key = api_key or os.getenv("BACKBOARD_API_KEY")
        if not self.api_key:
            raise ValueError("BACKBOARD_API_KEY not found in environment or parameters")
        
        self.default_thread_id = default_thread_id or os.getenv("BACKBOARD_THREAD_ID")
        self.client = BackboardClient(api_key=self.api_key)

    async def send_message(
        self, 
        content: str,
        thread_id: Optional[str] = None,
        memory: str = "Auto",
        stream: bool = False
    ) -> str:
        """
        统一的消息发送接口 - 作为所有 AI 请求的入口。
        
        这是一个高复用性的方法，可以被不同的服务调用：
        - PlanningService: 生成计划
        - ReminderService: 生成提醒建议
        - ChatAPI: 用户对话
        
        Args:
            content: 要发送的消息内容（可以是用户消息或系统 prompt）
            thread_id: 对话线程 ID，如果不提供则使用默认的
            memory: 记忆模式 - "Auto", "On", "Off"
                    - "Auto": AI 自动判断是否需要记忆
                    - "On": 强制记忆
                    - "Off": 不记忆
            stream: 是否流式返回（默认 False）
        
        Returns:
            AI 的回复内容
        
        Raises:
            ValueError: 如果没有提供 thread_id 且没有默认值
            Exception: 如果 API 调用失败
        """
        # 使用提供的 thread_id 或默认值
        active_thread_id = thread_id or self.default_thread_id
        if not active_thread_id:
            raise ValueError("thread_id is required (not provided and no default available)")
        
        print(f"📤 发送到 AI [thread={active_thread_id[:8]}...]: {content[:100]}...")

        try:
            response = await self.client.add_message(
                thread_id=active_thread_id,
                content=content,
                memory=memory,
                stream=False  # 暂时禁用 stream，因为需要完整响应
            )
            
            # response 是 MessageResponse 对象，直接访问 content 属性
            if hasattr(response, 'content'):
                ai_reply = response.content
            else:
                ai_reply = str(response)
            
            if ai_reply and len(ai_reply) > 100:
                print(f"🤖 AI 回复: {ai_reply[:100]}...")
            else:
                print(f"🤖 AI 回复: {ai_reply}")
            
            # 调试：检查是否产生了新记忆（如果 SDK 支持）
            # 注意：某些版本的 Backboard SDK 可能不返回 new_memories
            
            return ai_reply if ai_reply else ""

        except Exception as e:
            print(f"❌ AI 请求失败: {e}")
            raise Exception(f"Failed to get AI response: {str(e)}")

    async def send_user_message(self, content: str, thread_id: Optional[str] = None):
        """
        发送用户消息的便捷方法（向后兼容）。
        
        这是对 send_message() 的简单封装，专门用于处理用户的对话消息。
        
        Args:
            content: 用户消息内容
            thread_id: 可选的 thread ID，如果不提供则使用默认值
        
        Returns:
            AI 的回复
        """
        print(f"📤 用户说: {content}")
        
        try:
            ai_reply = await self.send_message(
                content=content,
                thread_id=thread_id,
                memory="Auto",  # 用户消息默认使用 Auto 模式
                stream=False
            )
            print(f"🤖 AI 回复: {ai_reply}")
            return ai_reply
        except Exception as e:
            print(f"❌ 发送失败: {e}")
            return "抱歉，我现在连不上大脑了。"

# --- 快速测试 ---
if __name__ == "__main__":
    chat = ChatService()
    
    # 模拟场景：你告诉它一个新计划
    msg = "Update: Next week (Jan 15-22), I'm going fishing everyday. Don't schedule any study sessions."
    
    asyncio.run(chat.send_user_message(msg))