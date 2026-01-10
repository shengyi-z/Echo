import asyncio
import sys
import os

# 将当前目录加入 Python 路径，确保能导入 services 模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.chat_service import ChatService

async def test_auto_memory():
    print("🧪 开始测试 ChatService (自动记忆功能)...\n")
    
    chat = ChatService()
    
    # --- 测试场景 1: 告诉它一个新事实 (Input Fact) ---
    # 我们设定一个比较独特的事实，方便验证
    fact_message = "Update: Next week (Monday to Friday), I will be going fishing everyday at the lake. No work allowed."
    print(f"1️⃣ [用户输入]: {fact_message}")
    
    reply1 = await chat.send_user_message(fact_message)
    print(f"🤖 [AI 回复]: {reply1}\n")
    
    # 关键步骤：稍微等待一下
    # 虽然对话上下文(Context Window)能立即记住，但我们要给 Backboard 一点时间
    # 去处理 memory="Auto" 的后台逻辑，确保持久化。
    print("⏳ 等待 5 秒，让记忆沉淀...")
    await asyncio.sleep(5)
    
    # --- 测试场景 2: 验证记忆 (Verify Recall) ---
    # 我们故意问一个模糊的问题，看它能不能关联到刚才的钓鱼计划
    query_message = "Generate a simple schedule for next Tuesday. What should I do?"
    print(f"\n2️⃣ [用户提问]: {query_message}")
    
    reply2 = await chat.send_user_message(query_message)
    print(f"🤖 [AI 回复]: {reply2}\n")
    
    # --- 简单的自动断言 ---
    if "fishing" in reply2.lower() or "lake" in reply2.lower():
        print("✅ 测试通过！AI 成功记住了你要去钓鱼。")
    else:
        print("⚠️ 测试警告：AI 似乎没有提到钓鱼，请检查 memory='Auto' 是否生效。")

if __name__ == "__main__":
    try:
        asyncio.run(test_auto_memory())
    except KeyboardInterrupt:
        print("\n测试已中断。")
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")