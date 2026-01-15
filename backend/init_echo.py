import asyncio
import os
import re
import requests
from pathlib import Path
from dotenv import load_dotenv
from backboard import BackboardClient

# 加载当前环境 (为了拿 API KEY)
load_dotenv()

BASE_URL = "https://app.backboard.io/api"

# 读取 system prompt
def load_system_prompt():
    """
    从 docs/planning_agent_prompt.md 读取 system prompt
    """
    prompt_path = Path(__file__).parent / "docs" / "planning_agent_prompt.md"
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"✅ System prompt 加载成功 ({len(content)} 字符)")
        return content
    except Exception as e:
        print(f"⚠️  无法加载 system prompt: {e}")
        return None

# ---------------------------------------------------------
# 核心功能：上传文档到 Assistant
# ---------------------------------------------------------
def upload_document_to_assistant(file_path: str, assistant_id: str):
    """
    上传文档到 Assistant
    """
    api_key = os.getenv("BACKBOARD_API_KEY")
    if not api_key:
        raise ValueError("BACKBOARD_API_KEY not found")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    headers = {"X-API-Key": api_key}
    
    try:
        filename = os.path.basename(file_path)
        
        with open(file_path, 'rb') as f:
            files = {
                'file': (filename, f, 'text/plain')
            }
            
            print(f"📤 上传文档: {filename}")
            print(f"🔍 Assistant ID: {assistant_id}")
            
            response = requests.post(
                f"{BASE_URL}/assistants/{assistant_id}/documents",
                files=files,
                headers=headers
            )
            
            print(f"🔍 响应状态: {response.status_code}")
            print(f"🔍 响应内容: {response.text}")
            
            response.raise_for_status()
            data = response.json()
            
            print(f"✅ 文档上传成功! Document ID: {data.get('document_id')}")
            print(f"   状态: {data.get('status')}")
            return data.get('document_id')
            
    except requests.exceptions.HTTPError as e:
        error_detail = e.response.text if hasattr(e.response, 'text') else str(e)
        print(f"❌ 上传失败 ({e.response.status_code}): {error_detail}")
        return None
    except Exception as e:
        print(f"⚠️ 文档上传失败: {e}")
        return None

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
    
    # 获取模型配置，默认使用 gemini-2.5-flash
    model = os.getenv("BACKBOARD_MODEL", "gemini-2.5-flash")
    print(f"🤖 使用模型: {model}")
    
    try:
        # 使用简洁的描述创建 assistant
        # 详细的 planning prompt 会在实际生成计划时作为消息发送
        assistant = await client.create_assistant(
            name="Echo Planning Agent",
            description="You are an expert planning assistant and life coach specializing in breaking down complex goals into actionable, time-bound execution plans. You create realistic, evidence-based plans with clear milestones, tasks, insights, and resources. You respond in structured JSON format when generating plans.",
            model=model
        )
        
        assistant_id = assistant.assistant_id
        print(f"✅ 助手创建成功! ID: {assistant_id}")
        
        # 上传规划文档
        docs_path = os.path.join(os.path.dirname(__file__), "docs", "Plan Builder.txt")
        if os.path.exists(docs_path):
            print("📚 上传助手文档...")
            upload_document_to_assistant(docs_path, assistant_id)
        else:
            print(f"⚠️ 文档未找到: {docs_path}")
        
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
    # API expects multipart/form-data, not JSON
    payload = {
        "content": user_input,
        "memory": "Auto",      # 开启自动记忆
        "web_search": "Auto",  # 开启联网搜索
        "stream": False        # 布尔值，不是字符串
    }
    
    print(f"🔍 发送的payload: {payload}")
    print(f"🔍 URL: {BASE_URL}/threads/{thread_id}/messages")
    
    try:
        # 使用 data= 发送 form data，不是 json=
        response = requests.post(
            f"{BASE_URL}/threads/{thread_id}/messages",
            data=payload,
            headers=headers
        )
        print(f"🔍 响应状态码: {response.status_code}")
        response.raise_for_status()
        data = response.json()
        
        # 根据API响应schema，content在返回的对象中
        content = data.get("content")
        if not content:
            # 如果content为空，尝试获取message字段
            content = data.get("message", "")
        
        print(f"\n📨 Backboard API 原始响应:")
        print(f"   Content: {content}")
        
        return content
    except requests.exceptions.HTTPError as e:
        error_detail = e.response.text if hasattr(e.response, 'text') else str(e)
        raise Exception(f"Backboard API error: {e.response.status_code} - {error_detail}")
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