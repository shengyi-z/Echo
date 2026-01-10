"""
Long-term Planning Assistant
核心功能：目标规划 + 进度追踪 + 智能提醒
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from backboard import BackboardClient
from config.settings import settings


class PlanningAssistant:
    """长期规划助手"""
    
    def __init__(self):
        self.client = BackboardClient(api_key=settings.BACKBOARD_API_KEY)
        self.assistant = None
        self.thread = None
        
    async def initialize(self):
        """初始化助手和对话线程"""
        
        # 定义工具
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web for information about courses, schools, visa requirements, etc.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query in Chinese or English"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_reminder",
                    "description": "Create a reminder for important deadlines or milestones",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Reminder title"
                            },
                            "date": {
                                "type": "string",
                                "description": "Date in YYYY-MM-DD format"
                            },
                            "description": {
                                "type": "string",
                                "description": "Detailed description of what to do"
                            },
                            "priority": {
                                "type": "string",
                                "enum": ["high", "medium", "low"],
                                "description": "Priority level"
                            }
                        },
                        "required": ["title", "date", "description"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "save_milestone",
                    "description": "Save a milestone or checkpoint for a long-term goal",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "goal_name": {
                                "type": "string",
                                "description": "Name of the main goal"
                            },
                            "milestone_name": {
                                "type": "string",
                                "description": "Name of this milestone"
                            },
                            "target_date": {
                                "type": "string",
                                "description": "Target completion date (YYYY-MM-DD)"
                            },
                            "action_items": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of specific actions to complete this milestone"
                            }
                        },
                        "required": ["goal_name", "milestone_name", "target_date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_plan_status",
                    "description": "Get current status of all active plans and goals",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "goal_filter": {
                                "type": "string",
                                "description": "Optional: filter by specific goal name"
                            }
                        }
                    }
                }
            }
        ]
        
        # 创建助手 - 带有详细的系统提示
        system_instruction = """你是一个专业的长期规划助手。你的核心职责：

1. **目标拆解 (Goal Breakdown)**
   - 当用户提出复杂目标时，将其分解为可执行的里程碑
   - 为每个里程碑设定合理的时间节点
   - 识别关键依赖关系（比如：申请签证前需要先准备材料）

2. **信息收集 (Information Gathering)**
   - 主动使用 web_search 工具查找：
     * 最新政策和要求（签证政策、考试要求等）
     * 性价比高的选择（培训班、驾校、课程等）
     * 时间线和截止日期
   - 整理信息，给出具体建议

3. **进度追踪 (Progress Tracking)**
   - 使用 save_milestone 保存每个里程碑
   - 定期询问用户进度
   - 识别风险和延迟

4. **智能提醒 (Smart Reminders)**
   - 为重要截止日期创建提醒
   - 提前提醒（比如：签证申请要提前3个月开始准备）
   - 根据依赖关系设置连锁提醒

**交互原则：**
- 用中文交流，清晰友好
- 主动提问，了解用户具体情况
- 给出可执行的具体建议，不要空泛
- 使用记忆功能记住用户的偏好和进度

**示例场景：**
用户："我想学法语并考出B2证书"
你应该：
1. 询问时间线、预算、当前水平
2. 搜索蒙特利尔的法语培训班
3. 拆解学习计划（词汇、语法、听力、口语、考试准备）
4. 设置里程碑（3个月后达到A2，6个月后达到B1等）
5. 创建提醒（每周学习检查点、报名截止日期等）
"""
        
        self.assistant = await self.client.create_assistant(
            name="长期规划助手",
            description="帮助用户规划和追踪长期目标的AI助手",
            instructions=system_instruction,
            tools=tools
        )
        
        # 创建主对话线程（带记忆）
        self.thread = await self.client.create_thread(self.assistant.assistant_id)
        
        print(f"✓ 助手已初始化")
        print(f"  Assistant ID: {self.assistant.assistant_id}")
        print(f"  Thread ID: {self.thread.thread_id}")
        
    async def chat(self, message: str) -> str:
        """发送消息并处理工具调用"""
        
        # 发送消息（启用记忆）
        response = await self.client.add_message(
            thread_id=self.thread.thread_id,
            content=message,
            memory="Auto",  # 自动记忆重要信息
            stream=False
        )
        
        # 处理工具调用
        if response.status == "REQUIRES_ACTION" and response.tool_calls:
            tool_outputs = []
            
            for tc in response.tool_calls:
                function_name = tc.function.name
                args = tc.function.parsed_arguments
                
                print(f"\n🔧 调用工具: {function_name}")
                print(f"   参数: {json.dumps(args, ensure_ascii=False, indent=2)}")
                
                # 执行工具
                result = await self._execute_tool(function_name, args)
                
                tool_outputs.append({
                    "tool_call_id": tc.id,
                    "output": json.dumps(result, ensure_ascii=False)
                })
            
            # 提交工具结果
            response = await self.client.submit_tool_outputs(
                thread_id=self.thread.thread_id,
                run_id=response.run_id,
                tool_outputs=tool_outputs
            )
        
        return response.content
    
    async def _execute_tool(self, function_name: str, args: Dict) -> Dict:
        """执行工具函数"""
        
        if function_name == "web_search":
            # 实际项目中，这里应该调用真实的搜索API
            # 这里用模拟数据演示
            query = args.get("query")
            return {
                "results": [
                    f"搜索结果：{query} 的相关信息...",
                    "建议查看蒙特利尔大学官网、魁北克移民局网站等"
                ]
            }
            
        elif function_name == "create_reminder":
            # 保存提醒到数据库或日历
            reminder = {
                "title": args.get("title"),
                "date": args.get("date"),
                "description": args.get("description"),
                "priority": args.get("priority", "medium"),
                "created_at": datetime.now().isoformat()
            }
            
            # 这里可以集成Google Calendar API或其他日历服务
            print(f"\n📅 已创建提醒:")
            print(f"   {reminder['title']} - {reminder['date']}")
            print(f"   {reminder['description']}")
            
            return {"status": "success", "reminder": reminder}
            
        elif function_name == "save_milestone":
            milestone = {
                "goal_name": args.get("goal_name"),
                "milestone_name": args.get("milestone_name"),
                "target_date": args.get("target_date"),
                "action_items": args.get("action_items", []),
                "status": "pending",
                "created_at": datetime.now().isoformat()
            }
            
            print(f"\n🎯 已保存里程碑:")
            print(f"   目标: {milestone['goal_name']}")
            print(f"   里程碑: {milestone['milestone_name']}")
            print(f"   截止日期: {milestone['target_date']}")
            
            return {"status": "success", "milestone": milestone}
            
        elif function_name == "get_plan_status":
            # 从数据库或Backboard记忆中获取计划状态
            return {
                "active_goals": [
                    {
                        "name": "学习法语考B2",
                        "progress": "20%",
                        "next_milestone": "完成A2水平测试"
                    }
                ]
            }
        
        return {"status": "unknown_function"}


async def main():
    """主程序"""
    assistant = PlanningAssistant()
    await assistant.initialize()
    
    print("\n" + "="*60)
    print("长期规划助手已启动！")
    print("="*60)
    print("\n示例使用：")
    print("  - '我想申请加拿大工作签证'")
    print("  - '帮我规划如何考出法语B2证书'")
    print("  - '我想在6个月内考取驾照'")
    print("  - '查看我当前所有目标的进度'")
    print("\n输入 'quit' 退出\n")
    
    while True:
        user_input = input("你: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q', '退出']:
            print("再见！记得按时完成你的目标哦 😊")
            break
        
        if not user_input:
            continue
        
        try:
            response = await assistant.chat(user_input)
            print(f"\n助手: {response}\n")
        except Exception as e:
            print(f"\n❌ 错误: {str(e)}\n")


if __name__ == "__main__":
    asyncio.run(main())