import requests

# 配置
HEADERS = {"X-API-Key": "espr_fOaXQW7733tsQ0-UaDmrMCLQDzS3aH-TlEasZx_vt0Y"}
BASE_URL = "https://app.backboard.io/api"

# 1. 创建规划助理 (只需执行一次)
def create_my_planner():
    payload = {
        "name": "Long-term Goal Assistant",
        "description": "你是一个专业的长期目标规划员..."
    }
    response = requests.post(f"{BASE_URL}/assistants", json=payload, headers=HEADERS)
    res_json = response.json()
    print(f"DEBUG: Created Assistant - {res_json}") # 打印出来看看
    return res_json["assistant_id"]

# 2. 发起一个新目标的对话 (比如考法语)
def start_new_goal(assistant_id):
    # 根据文档，这个接口路径是 /api/assistants/{assistant_id}/threads
    response = requests.post(f"{BASE_URL}/assistants/{assistant_id}/threads", json={}, headers=HEADERS)
    return response.json()["thread_id"]

# 3. 核心功能：拆解目标 + 联网搜索
def ask_assistant(thread_id, user_input):
    payload = {
        "content": user_input,
        "memory": "Auto",     # 开启自动记忆
        "web_search": "Auto", # 开启联网搜索
        "stream": "false"
    }
    response = requests.post(f"{BASE_URL}/threads/{thread_id}/messages", data=payload, headers=HEADERS)
    return response.json().get("content")

# 使用示例：
my_assistant_id = create_my_planner()
thread_id = start_new_goal(my_assistant_id)
print(ask_assistant(thread_id, "我想考法语B2，请帮我拆解目标并搜一下多伦多最有性价比的培训班"))