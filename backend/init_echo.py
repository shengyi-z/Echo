import asyncio
import os
import re
from dotenv import load_dotenv
from backboard import BackboardClient

# 加载当前环境 (为了拿 API KEY)
load_dotenv()

async def init_echo_auto():
    print("🚀 开始全自动初始化 Echo 系统...")
    
    # 1. 检查 API Key
    api_key = os.getenv("BACKBOARD_API_KEY")
    if not api_key:
        print("❌ 错误: .env 文件中未找到 BACKBOARD_API_KEY，请先配置 Key。")
        return

    client = BackboardClient(api_key=api_key)

    # ---------------------------------------------------------
    # 第一步：创建助手
    # ---------------------------------------------------------
    print("1️⃣ 正在招聘助手 (Creating Assistant)...")
    try:
        # SDK 简易模式：只传名字
        assistant = await client.create_assistant(name="Echo Daily Secretary")
        print(f"✅ 助手创建成功! ID: {assistant.assistant_id}")
    except Exception as e:
        print(f"❌ 创建助手失败: {e}")
        return

    # ---------------------------------------------------------
    # 第二步：创建线程
    # ---------------------------------------------------------
    print("2️⃣ 正在创建主线程 (Creating Thread)...")
    try:
        thread = await client.create_thread(assistant.assistant_id)
        print(f"✅ 线程创建成功! ID: {thread.thread_id}")
    except Exception as e:
        print(f"❌ 创建线程失败: {e}")
        return

    # ---------------------------------------------------------
    # 第三步：自动写入 .env 文件
    # ---------------------------------------------------------
    print("3️⃣ 正在自动写入 .env 配置...")
    try:
        update_env_file(assistant.assistant_id, thread.thread_id)
        print("✅ .env 文件更新成功！")
    except Exception as e:
        print(f"❌ 写入文件失败: {e}")
        print("⚠️ 请手动复制 ID:")
        print(f"BACKBOARD_ASSISTANT_ID={assistant.assistant_id}")
        print(f"BACKBOARD_THREAD_ID={thread.thread_id}")
        return

    print("\n" + "="*50)
    print("🎉 初始化全部完成！")
    print("现在你可以直接运行主程序了，无需任何手动操作。")
    print("="*50)

def update_env_file(asst_id, thread_id):
    """
    辅助函数：读取 .env，如果有旧的 ID 就替换，没有就追加
    """
    env_path = ".env"
    
    # 读取现有内容
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = ""

    # 定义替换或追加的逻辑
    def replace_or_append(text, key, value):
        pattern = f"^{key}=.*"
        # 如果 Key 存在，用正则替换
        if re.search(pattern, text, re.MULTILINE):
            return re.sub(pattern, f"{key}={value}", text, flags=re.MULTILINE)
        else:
            # 如果 Key 不存在，追加到末尾
            prefix = "\n" if text and not text.endswith("\n") else ""
            return text + prefix + f"{key}={value}\n"

    # 更新两个 ID
    content = replace_or_append(content, "BACKBOARD_ASSISTANT_ID", asst_id)
    content = replace_or_append(content, "BACKBOARD_THREAD_ID", thread_id)

    # 写回文件
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    asyncio.run(init_echo_auto())