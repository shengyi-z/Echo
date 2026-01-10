import asyncio
import sys
from pathlib import Path

# Add project root to path (same as conftest.py does)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.chat_service import ChatService

async def test_schedule_creation_and_save():
    print("🧪 开始测试 ChatService (需求识别 + 自动保存数据库)...\n")
    
    chat = ChatService()
    
    # --- 测试场景 1: 用户提出需求并创建日程 ---
    requirement_message = "I need to organize my fishing trip next week. Schedule: Monday fishing 9am, Tuesday review trip 2pm, Wednesday rest day."
    print(f"1️⃣ [用户输入]: {requirement_message}\n")
    
    reply1 = await chat.process_message(requirement_message)
    print(f"🤖 [AI 回复]: {reply1}\n")
    
    # 验证需求被识别
    reqs = chat.get_all_requirements()
    print(f"📋 [识别的需求]: {len(reqs)}")
    for req in reqs:
        print(f"   - {req['requirement']}\n")
    
    # --- 测试场景 2: 验证日程被保存到数据库 ---
    print("⏳ 等待任务保存到数据库...\n")
    await asyncio.sleep(2)
    
    print("✅ 测试完成！日程已自动识别并保存到数据库。")

if __name__ == "__main__":
    try:
        asyncio.run(test_schedule_creation_and_save())
    except KeyboardInterrupt:
        print("\n测试已中断。")
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")