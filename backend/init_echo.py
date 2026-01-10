import asyncio
import os
import re
import requests
from dotenv import load_dotenv
from backboard import BackboardClient

# 加载当前环境 (为了拿 API KEY)
load_dotenv()

BASE_URL = "https://app.backboard.io/api"

async def init_echo_auto():
    print("🚀 开始全自动初始化 Echo 系统...")
    
    # 1. 检查 API Key
    api_key = os.getenv("BACKBOARD_API_KEY")
    if not api_key:
        print("❌ 错误: .env 文件中未找到 BACKBOARD_API_KEY，请先配置 Key。")
        return

    client = BackboardClient(api_key=api_key)

    # ---------------------------------------------------------
    # 第一步：创建或复用助手
    # ---------------------------------------------------------
    print("1️⃣ 正在检查助手状态...")
    existing_asst_id = os.getenv("BACKBOARD_ASSISTANT_ID")
    
    if existing_asst_id:
        print(f"✅ 检测到已有助手 ID: {existing_asst_id}，直接复用")
        assistant_id = existing_asst_id
    else:
        print("   未检测到助手，正在创建新助手...")
        try:
            # 创建带描述的助手
            assistant = await client.create_assistant(
                name="Echo Daily Secretary",
                description="你是一个专业的长期目标规划员和生活助理。你会把目标拆解为可执行的里程碑，使用搜索工具寻找最有性价比的方案，并帮助用户管理日常任务。"
            )
            assistant_id = assistant.assistant_id
            print(f"✅ 助手创建成功! ID: {assistant_id}")
            
            # 写入 .env
            update_env_file("BACKBOARD_ASSISTANT_ID", assistant_id)
            print("✅ 助手 ID 已写入 .env")
        except Exception as e:
            print(f"❌ 创建助手失败: {e}")
            return

    # ---------------------------------------------------------
    # 第二步：创建线程
    # ---------------------------------------------------------
    print("2️⃣ 正在创建主线程 (Creating Thread)...")
    try:
        thread = await client.create_thread(assistant_id)
        print(f"✅ 线程创建成功! ID: {thread.thread_id}")
        
        # 写入 .env
        update_env_file("BACKBOARD_THREAD_ID", thread.thread_id)
        print("✅ 线程 ID 已写入 .env")
    except Exception as e:
        print(f"❌ 创建线程失败: {e}")
        return

    print("\n" + "="*50)
    print("🎉 初始化全部完成！")
    print("现在你可以直接运行主程序了，无需任何手动操作。")
    print("="*50)

# ---------------------------------------------------------
# 新增功能：发起新目标对话
# ---------------------------------------------------------
def start_new_goal(goal_description: str):
    """
    为一个新目标创建独立的对话线程
    例如：start_new_goal("我想考法语B2")
    """
    print(f"\n🎯 正在为目标创建新对话: {goal_description}")
    
    api_key = os.getenv("BACKBOARD_API_KEY")
    assistant_id = os.getenv("BACKBOARD_ASSISTANT_ID")
    
    if not api_key or not assistant_id:
        print("❌ 请先运行初始化: python init_echo.py")
        return None
    
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
        print(f"❌ 创建线程失败: {e}")
        return None

# ---------------------------------------------------------
# 新增功能：目标拆解 + 联网搜索
# ---------------------------------------------------------
def ask_with_search(thread_id: str, user_input: str):
    """
    核心功能：发送消息并开启自动记忆和联网搜索
    例如：ask_with_search(thread_id, "帮我拆解目标并搜一下多伦多最有性价比的法语培训班")
    """
    print(f"\n💬 正在处理: {user_input[:50]}...")
    
    api_key = os.getenv("BACKBOARD_API_KEY")
    if not api_key:
        print("❌ 请先配置 BACKBOARD_API_KEY")
        return None
    
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
        
        print("✅ 回复:")
        print(content)
        return content
    except Exception as e:
        print(f"❌ 发送消息失败: {e}")
        return None

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
# 使用示例
# ---------------------------------------------------------
def example_usage():
    """
    演示如何使用新功能
    """
    # 1. 先初始化系统（如果还没初始化）
    # asyncio.run(init_echo_auto())
    
    # 2. 为新目标创建对话
    thread_id = start_new_goal("我想考法语B2")
    
    if thread_id:
        # 3. 使用联网搜索拆解目标
        ask_with_search(
            thread_id, 
            "请帮我拆解这个目标为具体步骤，并搜索多伦多最有性价比的法语培训班"
        )

if __name__ == "__main__":
    # 正常初始化
    asyncio.run(init_echo_auto())
    
    # 如果想测试新功能，取消下面的注释：
    example_usage()