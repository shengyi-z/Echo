"""
Backboard 简化版测试
"""
import asyncio
from backboard import BackboardClient
from dotenv import load_dotenv
import os

load_dotenv()

async def simple_test():
    print("🧪 Backboard 快速测试\n")
    
    # 1. 初始化客户端
    print("1️⃣ 初始化客户端...")
    api_key = os.getenv("BACKBOARD_API_KEY")
    client = BackboardClient(api_key=api_key)
    print("✅ 客户端创建成功\n")
    
    # 2. 创建助手 - 使用最简单的参数
    print("2️⃣ 创建助手...")
    try:
        assistant = await client.create_assistant(
            name="简单测试助手"
        )
        print(f"✅ 助手创建成功!")
        print(f"   ID: {assistant.assistant_id}\n")
    except Exception as e:
        print(f"❌ 创建助手失败: {e}\n")
        return
    
    # 3. 创建对话线程
    print("3️⃣ 创建对话线程...")
    try:
        thread = await client.create_thread(assistant.assistant_id)
        print(f"✅ 线程创建成功!")
        print(f"   ID: {thread.thread_id}\n")
    except Exception as e:
        print(f"❌ 创建线程失败: {e}\n")
        return
    
    # 4. 发送消息
    print("4️⃣ 发送测试消息...")
    try:
        response = await client.add_message(
            thread_id=thread.thread_id,
            content="你好，请简单回复'测试成功'即可。",
            stream=False
        )
        print(f"✅ 收到回复!")
        print(f"   内容: {response.content[:100]}\n")
    except Exception as e:
        print(f"❌ 发送消息失败: {e}\n")
        return
    
    # 5. 测试记忆功能
    print("5️⃣ 测试记忆功能...")
    try:
        # 分享信息
        await client.add_message(
            thread_id=thread.thread_id,
            content="请记住：我叫张三。",
            memory="Auto",
            stream=False
        )
        
        # 等待记忆生效
        await asyncio.sleep(2)
        
        # 测试回忆
        response = await client.add_message(
            thread_id=thread.thread_id,
            content="我叫什么名字？",
            memory="Auto",
            stream=False
        )
        
        if "张三" in response.content:
            print(f"✅ 记忆功能正常!")
            print(f"   回复: {response.content[:100]}\n")
        else:
            print(f"⚠️  记忆功能可能不正常")
            print(f"   回复: {response.content[:100]}\n")
    except Exception as e:
        print(f"❌ 记忆测试失败: {e}\n")
    
    print("="*60)
    print("🎉 基本功能测试完成！")
    print("="*60)
    print("\n下一步:")
    print("  - 如果所有测试通过，可以运行主程序了")
    print("  - python3 main.py")
    print("  - 或 streamlit run streamlit_app.py")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(simple_test())