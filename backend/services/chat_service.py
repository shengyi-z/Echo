import os
import asyncio
from backboard import BackboardClient
from dotenv import load_dotenv

load_dotenv()

class ChatService:
    def __init__(self):
        self.api_key = os.getenv("BACKBOARD_API_KEY")
        self.thread_id = os.getenv("BACKBOARD_THREAD_ID")
        self.client = BackboardClient(api_key=self.api_key)

    async def send_user_message(self, content: str):
        """
        发送用户消息，并让 AI 自动判断是否需要记忆。
        """
        print(f"📤 用户说: {content}")

        try:
            # 关键点在这里！！！
            # memory="Auto" 告诉 Backboard：
            # "请分析这句话，如果有长期价值的信息（比如计划、偏好），请自动存下来。"
            response = await self.client.add_message(
                thread_id=self.thread_id,
                content=content,
                memory="Auto",   # <--- 核心魔法开关
                stream=False
            )
            
            ai_reply = response.content
            print(f"🤖 AI 回复: {ai_reply}")
            
            # 我们可以检查一下它这次有没有产生新记忆 (用于调试)
            # 注意：SDK 返回结构可能略有不同，视版本而定，但这不影响核心功能
            if hasattr(response, 'new_memories') and response.new_memories:
                print(f"✨ [自动触发记忆]: {response.new_memories}")
            
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