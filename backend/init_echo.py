import asyncio
import os
import re
import requests
from dotenv import load_dotenv
from backboard import BackboardClient

# 加载当前环境 (为了拿 API KEY)
load_dotenv()

BASE_URL = "https://app.backboard.io/api"

# ---------------------------------------------------------
# 核心功能：确保助手已初始化
# ---------------------------------------------------------
async def ensure_assistant():
    """
    确保助手存在，如果不存在则创建
    返回 assistant_id
    """
    api_key = os.getenv("BACKBOARD_API_KEY")
    if not api_key:
        raise ValueError("BACKBOARD_API_KEY not found in .env")
    
    existing_asst_id = os.getenv("BACKBOARD_ASSISTANT_ID")
    
    if existing_asst_id:
        print(f"✅ 使用已有助手 ID: {existing_asst_id}")
        return existing_asst_id
    
    # 创建新助手
    print("🔧 正在创建新助手...")
    client = BackboardClient(api_key=api_key)
    
    try:
        assistant = await client.create_assistant(
            name="Echo Daily Secretary",
            description="你是一个专业的长期目标规划员和生活助理。你会把目标拆解为可执行的里程碑，使用搜索工具寻找最有性价比的方案，并帮助用户管理日常任务。"
        )
        assistant_id = assistant.assistant_id
        print(f"✅ 助手创建成功! ID: {assistant_id}")
        
        # 写入 .env
        update_env_file("BACKBOARD_ASSISTANT_ID", assistant_id)
        return assistant_id
    except Exception as e:
        raise Exception(f"创建助手失败: {e}")

# ---------------------------------------------------------
# 核心功能：创建新对话线程
# ---------------------------------------------------------
def create_thread(assistant_id: str = None):
    """
    为用户创建独立的对话线程
    返回 thread_id
    """
    api_key = os.getenv("BACKBOARD_API_KEY")
    if not assistant_id:
        assistant_id = os.getenv("BACKBOARD_ASSISTANT_ID")
    
    if not api_key or not assistant_id:
        raise ValueError("Missing API key or assistant ID")
    
    headers = {"X-API-Key": api_key}
    
    try:
        response = requests.post(
            f"{BASE_URL}/assistants/{assistant_id}/threads",
            json={},
            headers=headers
        )
        response.raise_for_status()
        thread_id = response.json()["thread_id"]
        print(f"✅ 新线程创建成功! ID: {thread_id}")
        return thread_id
    except Exception as e:
        raise Exception(f"创建线程失败: {e}")

# ---------------------------------------------------------
# 核心功能：发送消息 + 联网搜索
# ---------------------------------------------------------
def send_message(thread_id: str, user_input: str):
    """
    发送消息并开启自动记忆和联网搜索
    返回 AI 回复内容
    """
    api_key = os.getenv("BACKBOARD_API_KEY")
    if not api_key:
        raise ValueError("BACKBOARD_API_KEY not found")
    
    headers = {"X-API-Key": api_key}
    payload = {
        "content": user_input,
        "memory": "Auto",      # 开启自动记忆
        "web_search": "Auto",  # 开启联网搜索
        "stream": "false"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/threads/{thread_id}/messages",
            data=payload,
            headers=headers
        )
        response.raise_for_status()
        content = response.json().get("content")
        return content
    except Exception as e:
        raise Exception(f"发送消息失败: {e}")

def update_env_file(key: str, value: str):
    """
    辅助函数：读取 .env，如果有旧的 Key 就替换，没有就追加
    """
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    
    # 读取现有内容
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = ""

    # 定义替换或追加的逻辑
    pattern = f"^{key}=.*"
    # 如果 Key 存在，用正则替换
    if re.search(pattern, content, re.MULTILINE):
        content = re.sub(pattern, f"{key}={value}", content, flags=re.MULTILINE)
    else:
        # 如果 Key 不存在，追加到末尾
        prefix = "\n" if content and not content.endswith("\n") else ""
        content = content + prefix + f"{key}={value}\n"

    # 写回文件
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(content)

# ---------------------------------------------------------
# 完整初始化流程（仅用于命令行测试）
# ---------------------------------------------------------
async def init_echo_auto():
    """
    完整初始化流程：创建助手 + 创建默认线程
    """
    print("🚀 开始全自动初始化 Echo 系统...")
    
    try:
        # 1. 确保助手存在
        assistant_id = await ensure_assistant()
        
        # 2. 创建默认线程
        print("2️⃣ 正在创建主线程...")
        thread_id = create_thread(assistant_id)
        
        # 写入 .env
        update_env_file("BACKBOARD_THREAD_ID", thread_id)
        print("✅ 线程 ID 已写入 .env")
        
        print("\n" + "="*50)
        print("🎉 初始化全部完成！")
        print("="*50)
    except Exception as e:
        print(f"❌ 初始化失败: {e}")

# ---------------------------------------------------------
# 命令行测试
# ---------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(init_echo_auto())