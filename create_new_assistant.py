#!/usr/bin/env python3
"""
创建新的 Assistant（使用 Claude）
"""

import asyncio
import os
from dotenv import load_dotenv

os.chdir("/Users/shengyizhong/Personal/Echo")
load_dotenv()


async def init_with_claude():
    print("\n" + "=" * 70)
    print("🚀 创建新 Assistant（Claude 模型）")
    print("=" * 70)

    # 步骤 1: 清空旧的 ID
    print("\n1️⃣  清除旧的 Assistant ID...")
    with open(".env", "r") as f:
        content = f.read()

    # 清空 ASSISTANT_ID 和 THREAD_ID
    content = content.replace(
        "BACKBOARD_ASSISTANT_ID=b8a8d220-af90-4e59-803a-44cdb4d332fe",
        "BACKBOARD_ASSISTANT_ID="
    )
    content = content.replace(
        "BACKBOARD_THREAD_ID=58da4163-cf6d-42b5-9871-fe80fa39db7d",
        "BACKBOARD_THREAD_ID="
    )

    with open(".env", "w") as f:
        f.write(content)

    # 重新加载环境变量
    load_dotenv(override=True)

    print("   ✅ 旧 ID 已清空")

    # 步骤 2: 创建新 Assistant
    print("\n2️⃣  创建新 Assistant...")

    from backend.init_echo import ensure_assistant, create_thread

    try:
        assistant_id = await ensure_assistant()
        print(f"   ✅ 新 Assistant ID: {assistant_id}")

        # 步骤 3: 创建新 Thread
        print("\n3️⃣  创建新对话线程...")
        thread_id = create_thread(assistant_id)
        print(f"   ✅ 新 Thread ID: {thread_id}")

        print("\n" + "=" * 70)
        print("✅ 完成！新 Assistant 已创建（使用 Claude）")
        print("=" * 70)
        print(f"""
✨ 新配置已保存到 .env：
   Assistant ID: {assistant_id}
   Thread ID: {thread_id}
   模型: anthropic:claude-3-sonnet

现在可以启动应用：
   python -m uvicorn backend.main:app --reload
""")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(init_with_claude())
