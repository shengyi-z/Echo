import asyncio
import os
import re
import requests
from pathlib import Path
from dotenv import load_dotenv
from backboard import BackboardClient

from .utils.tools import AVAILABLE_TOOLS

# 加载当前环境 (为了拿 API KEY)
load_dotenv()

BASE_URL = "https://app.backboard.io/api"

# 读取 system prompt
def load_system_prompt():
    """
    从 docs/planning_agent_prompt.md 读取 system prompt
    并转义所有的大括号以避免被当作 LangChain 模板变量
    """
    prompt_path = Path(__file__).parent / "docs" / "planning_agent_prompt.md"
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 转义所有单个大括号为双大括号，避免 LangChain 模板错误
        # {variable} -> {{variable}}
        content = content.replace('{', '{{').replace('}', '}}')
        
        print(f"✅ System prompt 加载成功 ({len(content)} 字符，已转义大括号)")
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
    
    # 加载完整的 system prompt 作为 instructions
    system_prompt = load_system_prompt()
    if not system_prompt:
        raise ValueError("无法加载 system prompt，assistant 创建失败")
    
    try:
        # 使用完整的 system prompt 作为 system_prompt，并传递工具
        assistant = await client.create_assistant(
            name="Echo Planning Agent",
            description="An assistant specialized in generating and managing plans and tasks for users.",
            system_prompt=system_prompt,
            tools=AVAILABLE_TOOLS
        )
        
        assistant_id = assistant.assistant_id
        print(f"✅ 助手创建成功! ID: {assistant_id}")
        print(f"🔧 已注册 {len(AVAILABLE_TOOLS)} 个工具")
        
        # 写入 .env
        update_env_file("BACKBOARD_ASSISTANT_ID", assistant_id)
        return assistant_id
    except Exception as e:
        print(f"❌ 创建助手失败: {e}")
        print(f"❌ 错误类型: {type(e)}")
        import traceback
        traceback.print_exc()
        raise Exception(f"创建助手失败: {e}")

# ---------------------------------------------------------
# 核心功能：创建新对话线程
# ---------------------------------------------------------
async def create_thread(assistant_id: str = None):
    """
    为用户创建独立的对话线程
    返回 thread_id
    """
    api_key = os.getenv("BACKBOARD_API_KEY")
    if not assistant_id:
        assistant_id = os.getenv("BACKBOARD_ASSISTANT_ID")
    
    if not api_key or not assistant_id:
        raise ValueError("Missing API key or assistant ID")
    
    try:
        client = BackboardClient(api_key=api_key)
        thread = await client.create_thread(assistant_id=assistant_id)
        thread_id = thread.thread_id
        print(f"✅ 新线程创建成功! ID: {thread_id}")
        return thread_id
    except Exception as e:
        raise Exception(f"创建线程失败: {e}")

# ---------------------------------------------------------
# 核心功能：发送消息 + 联网搜索
# ---------------------------------------------------------
async def send_message(thread_id: str, user_input: str) -> str:
    """
    使用 BackboardClient SDK 发送消息并开启自动记忆和联网搜索
    支持工具调用并自动处理工具响应
    返回 AI 回复内容
    """
    from .utils.tools import TOOL_HANDLERS
    
    api_key = os.getenv("BACKBOARD_API_KEY")
    if not api_key:
        raise ValueError("BACKBOARD_API_KEY not found")
    provider = os.getenv("BACKBOARD_PROVIDER", "anthropic")
    model = os.getenv("BACKBOARD_MODEL", "claude-sonnet-4-20250514")
    try:
        client = BackboardClient(api_key=api_key)
        
        print(f"📤 发送消息到 thread_id: {thread_id}")
        print(f"📝 用户消息: {user_input[:100]}...")
        
        # 使用 SDK 的 add_message 方法
        response = await client.add_message(
            thread_id=thread_id,
            content=user_input,
            memory="Auto",       # 开启自动记忆
            # web_search="Auto",   # 开启联网搜索
            stream=False,
        )
        
        print(f"\n📨 Backboard SDK 响应类型: {type(response)}")
        print(f"📨 响应对象属性: {dir(response)}")
        
        # 检查是否有工具调用请求
        if response.status == "REQUIRES_ACTION" and response.tool_calls:
            print(f"\n🔧 检测到工具调用: {len(response.tool_calls)} 个")
            
            # 准备工具输出
            tool_outputs = []
            for tool_call in response.tool_calls:
                tool_name = tool_call.function.name
                tool_call_id = tool_call.id
                print(f"   - 工具: {tool_name} (ID: {tool_call_id})")
                
                # 执行工具
                if tool_name in TOOL_HANDLERS:
                    tool_result = TOOL_HANDLERS[tool_name]()
                    print(f"   - 结果: {tool_result}")
                    
                    tool_outputs.append({
                        "tool_call_id": tool_call_id,
                        "output": tool_result
                    })
                else:
                    print(f"   ⚠️ 未找到工具处理器: {tool_name}")
                    tool_outputs.append({
                        "tool_call_id": tool_call_id,
                        "output": f"Error: Tool {tool_name} not found"
                    })
            
            # 使用 submit_tool_outputs 提交工具结果
            if tool_outputs and hasattr(response, 'run_id'):
                print(f"\n📤 提交工具输出到 run_id: {response.run_id}")
                response = await client.submit_tool_outputs(
                    thread_id=thread_id,
                    run_id=response.run_id,
                    tool_outputs=tool_outputs
                )
                print(f"   ✅ 工具结果已提交，新状态: {response.status}")
        
        # 获取最终的 AI 响应内容
        if hasattr(response, 'content'):
            content = response.content
        else:
            content = str(response)
            
        if not content:
            print(f"⚠️ 响应内容为空！完整响应对象: {response}")
            raise Exception(f"Backboard SDK 返回了空内容")
        
        print(f"\n✅ AI 完整响应:")
        print(f"   {content}")
        print("="*80)
        
        return content
    except Exception as e:
        print(f"❌ 发送消息失败: {e}")
        import traceback
        traceback.print_exc()
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