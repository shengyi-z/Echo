"""
更新assistant的description，让它遵循上传的Planning Agent文档
"""
import os
import requests
from dotenv import load_dotenv
from pathlib import Path

# 加载环境变量
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

BASE_URL = "https://app.backboard.io/api"

def update_assistant_description():
    api_key = os.getenv("BACKBOARD_API_KEY")
    assistant_id = os.getenv("BACKBOARD_ASSISTANT_ID")
    
    if not api_key or not assistant_id:
        print("❌ 缺少 API key 或 assistant ID")
        return
    
    # 新的system_prompt - 告诉AI要遵循上传的文档
    new_system_prompt = """你是Echo规划助理，专门帮助用户制定和执行长期目标计划。

🎯 核心职责：
1. 当用户提到目标、计划、学习、健身等需要规划的事项时，你必须严格遵循已上传的"Plan Builder"
2. 必须按照文档中的Response Format返回完整的JSON结构，包含：
   - response_to_user: 温暖鼓励的总结
   - milestones: 3-5个里程碑，每个带target_date和tasks
   - insights: overview, key_points, progression_guidelines, scientific_basis, adjustments
   - resources: 相关资源链接
3. 对于普通聊天对话，提供友好、支持性的回复
4. 积极使用web search工具查找最新资源和最佳实践

⚠️ 重要规则：
- 当用户说"我想学习X"、"帮我制定Y计划"时，立即启用Planning Agent模式
- 所有日期必须是YYYY-MM-DD格式，从今天开始合理递增
- 返回的JSON必须可以被正确解析
- 严格遵循文档中定义的Response Format，不要遗漏任何必需字段"""
    
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        # 先查询当前assistant信息
        print(f"🔍 查询当前assistant信息...")
        get_response = requests.get(
            f"{BASE_URL}/assistants/{assistant_id}",
            headers=headers
        )
        print(f"GET 状态码: {get_response.status_code}")
        if get_response.ok:
            current = get_response.json()
            print(f"当前名称: {current.get('name')}")
            print(f"当前描述: {current.get('description', 'N/A')[:100]}...")
        
        # 使用PUT更新assistant（根据API文档）
        print(f"\n📝 更新assistant system prompt...")
        response = requests.put(
            f"{BASE_URL}/assistants/{assistant_id}",
            json={
                "name": "Echo Planning Assistant",
                "system_prompt": new_system_prompt
            },
            headers=headers
        )
        
        print(f"PUT 状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Assistant更新成功!")
            print(f"   名称: {data.get('name')}")
            print(f"   新描述: {data.get('description')}")
        else:
            print(f"❌ 更新失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    update_assistant_description()
