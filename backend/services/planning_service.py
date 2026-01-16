from datetime import date, timedelta
from typing import List, Mapping, Dict, Any, Optional
import json
import re
import os
from pathlib import Path

from sqlalchemy.orm import Session
from uuid import UUID

from ..repo.goal_repo import GoalRepository
from ..schemas.plan import PlanRequest, PlanResponse, PlanMilestone, PlanTask, PlanArtifact, PlanInsights, PlanResource
from .chat_service import ChatService


# Load the planning agent prompt template
def load_planning_prompt_template():
    """Load the planning agent instruction document"""
    prompt_path = Path(__file__).parent.parent / \
        "docs" / "planning_agent_prompt.md"
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"⚠️  无法加载 planning prompt: {e}")
        return None


# Planning workflow orchestration for plan generation + persistence.
class PlanningService:
    def __init__(self, session: Session):
        # DB session is injected so callers control lifecycle.
        self.session = session
        self.goal_repo = GoalRepository(session)
        self.chat_service = ChatService()

    # Public entrypoint: generate a plan using AI and store it in the DB.
    async def generate_and_store(self, request: PlanRequest) -> PlanResponse:
        if not request.goal:
            raise ValueError("goal is required to generate a plan")

        if not request.thread_id:
            raise ValueError("thread_id is required to generate AI-based plan")

        # Use memory_id from request if provided, otherwise use thread_id
        memory_id = request.memory_id or request.thread_id
        if not memory_id:
            raise ValueError(
                "memory_id or thread_id is required to store the plan")

        # Step 1: Construct AI prompt for plan generation
        prompt = self._build_planning_prompt(request)

        # Step 2: Call AI to generate the plan
        ai_response = None
        try:
            ai_response = await self.chat_service.send_message(
                content=prompt,
                thread_id=request.thread_id,
                memory="Auto"
            )
        except Exception as e:
            # Fallback to default plan if AI fails
            print(f"⚠️ AI call failed: {e}. Using default plan.")
            milestones_payload = self._build_milestones_payload(request)
        else:
            # Step 3: Parse AI response into structured data
            milestones_payload = self._parse_ai_response(ai_response, request)

        # Step 4: Store the plan in database
        goal = self.goal_repo.create_goal(
            memory_id=memory_id,
            title=request.goal.title,
            type=request.goal.type.value,
            deadline=request.goal.deadline,
            budget=request.goal.budget,
            weekly_hours=request.goal.weekly_hours,
            status="not-started",
            milestones=milestones_payload,
        )
        self.session.commit()

        # Reload with children so we can format a full response.
        stored_goal = self.goal_repo.get_goal(goal.id, include_children=True)
        if not stored_goal:
            raise ValueError("failed to load stored plan")

        # Map stored entities into response schemas.
        # Build tasks indexed by milestone for nesting
        tasks_by_milestone = {}
        for task in stored_goal.tasks:
            milestone_id = str(task.milestone_id)
            if milestone_id not in tasks_by_milestone:
                tasks_by_milestone[milestone_id] = []
            tasks_by_milestone[milestone_id].append(
                PlanTask(
                    id=str(task.id),
                    title=task.title,
                    due_date=task.due_date,
                    milestone_id=milestone_id,
                    priority=task.priority,
                    estimated_time=task.estimated_time,
                )
            )

        # Create milestones with nested tasks
        milestones = [
            PlanMilestone(
                id=str(milestone.id),
                title=milestone.title,
                target_date=milestone.target_date,
                definition_of_done=milestone.definition_of_done,
                order=milestone.order,
                tasks=tasks_by_milestone.get(str(milestone.id), []),
            )
            for milestone in stored_goal.milestones
        ]
        tasks = []

        # Parse insights and resources from AI response
        if ai_response:
            insights, resources = self._parse_insights_and_resources(
                ai_response)
        else:
            insights, resources = None, []

        # Return a structured plan response for the client.
        return PlanResponse(
            date=date.today(),
            focus=stored_goal.title,
            milestones=milestones,
            tasks=tasks,
            artifacts=[],
            insights=insights,
            resources=resources,
            message="✅ AI-generated plan created and stored successfully.",
            warnings=[],
        )

    # Construct the prompt to send to AI for plan generation
    def _build_planning_prompt(self, request: PlanRequest) -> str:
        """
        Build a detailed prompt for the AI to generate a structured plan using the 
        planning agent instruction document with filled-in variables.
        """
        goal = request.goal
        budget_str = f"${goal.budget}" if goal.budget else "Flexible"
        hours_str = str(goal.weekly_hours) if goal.weekly_hours else "Flexible"
        today = date.today().strftime("%Y-%m-%d")

        # Load the planning prompt template
        template = load_planning_prompt_template()

        if template:
            # Fill in the template variables
            # Note: The template uses these as examples, not actual template strings
            # We'll append the actual goal info at the end
            filled_prompt = template + f"""

---

## Current Planning Request

**Goal Information:**
- Title: {goal.title}
- Type: {goal.type.value}
- Deadline: {goal.deadline.strftime("%Y-%m-%d")}
- Budget: {budget_str}
- Weekly Available Hours: {hours_str}
- Current Date: {today}

Please generate a complete, structured plan following all the rules and format specifications above.
"""
            return filled_prompt

        # Fallback to simplified prompt if template loading fails
        prompt = f"""
I need you to help me create a **detailed, executable plan with a clear timeline** to achieve the following goal:

    **目标信息：**
    - 标题：{goal.title}
    - 类型：{goal.type.value}
    - 截止日期：{goal.deadline}
    - 预算：{budget_str}
    - 每周可投入时间：{hours_str}
    - 今天的日期：{today}

    **核心规则（重要）：**
    1. 对于单个日程/事件：不要自行安排额外计划，只需列出该任务本身。可以针对该任务提出建议（recommendation）但不要主动添加相关任务。
    2. 对于长期计划（如健身、学习等）：
       - 需要根据用户的身体状况/背景知识来制定
       - 提供一个简洁可行的长期安排框架
       - 该框架必须足够灵活，用户可以根据实际情况调整
       - 所有建议必须有科学依据支持
       - 包含具体的调整指南（如感觉过度训练时如何调整）
    3. **重要：所有日期必须是具体的日期（YYYY-MM-DD格式），且从{today}开始合理递增。不要使用相对时间如"Week 1"，只能用作描述性标签。**

    **任务要求：**
    1. 将这个目标拆解为 3-5 个关键里程碑（Milestones），每个里程碑有明确的起始和截止日期
    2. 为每个里程碑定义清晰的完成标准（Definition of Done）
    3. 为前 2-3 个里程碑创建 5-8 个具体的、可执行的任务（Tasks），每个任务有具体的due_date
    4. 使用你的 web search 工具查找相关资源、最佳实践和建议
    5. 考虑用户的预算和时间限制
    6. 所有任务的due_date必须在对应里程碑的target_date之前或相等

    **输出格式（严格按照此格式）：**
    请以 JSON 格式返回计划，结构如下：

    {{
    "milestones": [
        {{
        "title": "里程碑标题（带周期说明，如：第1周 - 基础建立）",
        "target_date": "YYYY-MM-DD（具体日期）",
        "definition_of_done": "完成标准描述",
        "order": 1,
        "tasks": [
            {{
            "title": "任务标题",
            "due_date": "YYYY-MM-DD（具体日期，不超过target_date）",
            "priority": "high/medium/low",
            "estimated_time": 2.5
            }}
        ]
        }}
    ],
    "insights": {{
        "overview": "计划总体概述和关键目标",
        "key_points": ["关键点1", "关键点2", "关键点3"],
        "progression_guidelines": "逐周或逐阶段的详细进展指南，包括每个阶段的时间范围",
        "scientific_basis": "科学依据和最佳实践引用",
        "adjustments": "灵活调整指南"
    }},
    "resources": [
        {{"title": "资源标题", "url": "https://...", "category": "category_name"}}
    ]
    }}

    请确保：
    - 所有日期都是具体的YYYY-MM-DD格式
    - 日期合理递增，从{today}开始
    - 任务可执行且具体
    - 时间线清晰，适合显示在日历上
    """
        return prompt

    # Parse AI response into milestone/task payload format
    def _parse_ai_response(self, ai_response: str, request: PlanRequest) -> List[Mapping[str, object]]:
        """
        Parse AI's JSON response and convert it into database payload format.
        Falls back to default plan if parsing fails.
        """
        try:
            # Extract JSON from AI response (it might be wrapped in markdown code blocks)
            json_match = re.search(
                r'```json\s*(.*?)\s*```', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON object directly
                json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("No JSON found in AI response")

            plan_data = json.loads(json_str)
            milestones = plan_data.get("milestones", [])

            if not milestones:
                raise ValueError("No milestones found in AI response")

            # Convert AI format to database payload format
            milestones_payload = []
            for idx, milestone in enumerate(milestones, 1):
                tasks = milestone.get("tasks", [])
                milestone_payload = {
                    "title": milestone.get("title", f"Milestone {idx}"),
                    "target_date": self._parse_date(milestone.get("target_date"), request.goal.deadline),
                    "definition_of_done": milestone.get("definition_of_done", "To be defined"),
                    "order": milestone.get("order", idx),
                    "status": "not-started",
                    "tasks": [
                        {
                            "title": task.get("title", "Unnamed task"),
                            "due_date": self._parse_date(task.get("due_date"), request.goal.deadline),
                            "priority": task.get("priority", "medium"),
                            "estimated_time": task.get("estimated_time", 1.0),
                        }
                        for task in tasks
                    ]
                }
                milestones_payload.append(milestone_payload)

            return milestones_payload

        except Exception as e:
            print(f"⚠️ Failed to parse AI response: {e}")
            print(f"AI Response: {ai_response[:500]}...")
            # Fallback to default plan
            return self._build_milestones_payload(request)

    # Parse insights and resources from AI response
    def _parse_insights_and_resources(self, ai_response: str) -> tuple[Optional[PlanInsights], List[PlanResource]]:
        """
        Extract structured insights and resource links from AI response.
        """
        insights = None
        resources = []

        try:
            # Try to extract JSON from AI response
            json_match = re.search(
                r'```json\s*(.*?)\s*```', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    # No JSON found, use raw text as insights
                    insights = PlanInsights(raw_text=ai_response)
                    return insights, resources

            plan_data = json.loads(json_str)

            # Extract insights
            insights_data = plan_data.get("insights", {})
            if isinstance(insights_data, str):
                insights = PlanInsights(raw_text=insights_data)
            elif isinstance(insights_data, dict):
                insights = PlanInsights(
                    overview=insights_data.get("overview"),
                    key_points=insights_data.get("key_points", []),
                    precautions=insights_data.get("precautions", []),
                    progression_guidelines=insights_data.get(
                        "progression_guidelines"),
                    scientific_basis=insights_data.get("scientific_basis"),
                    adjustments=insights_data.get("adjustments"),
                    raw_text=insights_data.get("raw_text"),
                )

            # Extract resources
            resources_data = plan_data.get("resources", [])
            for resource in resources_data:
                if isinstance(resource, str):
                    resources.append(PlanResource(url=resource))
                elif isinstance(resource, dict):
                    resources.append(PlanResource(
                        title=resource.get("title"),
                        url=resource.get("url", ""),
                        category=resource.get("category"),
                    ))

            return insights, resources

        except Exception as e:
            print(f"⚠️ Failed to parse insights and resources: {e}")
            # Return raw text as fallback
            insights = PlanInsights(raw_text=ai_response)
            return insights, resources

    # Helper to parse date strings with fallback
    def _parse_date(self, date_str: Optional[str], fallback: date) -> date:
        """
        Parse date string in YYYY-MM-DD format. Returns fallback if parsing fails.
        """
        if not date_str:
            return fallback
        try:
            from datetime import datetime
            parsed = datetime.strptime(date_str, "%Y-%m-%d").date()
            # Ensure date is not in the past
            today = date.today()
            if parsed < today:
                return today
            return parsed
        except Exception:
            return fallback

    # Build initial milestone/task payloads for a fallback/default plan.
    def _build_milestones_payload(self, request: PlanRequest) -> List[Mapping[str, object]]:
        today = date.today()
        deadline = request.goal.deadline
        target_date = self._clamp_date(
            min(deadline, today + timedelta(days=14)), today)

        tasks = self._default_tasks(deadline=deadline, today=today)

        return [
            {
                "title": f"Kickoff: {request.goal.title}",
                "target_date": target_date,
                "definition_of_done": "Initial plan, resources, and schedule are in place.",
                "order": 1,
                "status": "not-started",
                "tasks": tasks,
            }
        ]

    # Default starter tasks before LLM-based planning is added.
    def _default_tasks(self, *, deadline: date, today: date) -> List[Mapping[str, object]]:
        def _due_in(days: int) -> date:
            return self._clamp_date(min(deadline, today + timedelta(days=days)), today)

        return [
            {
                "title": "Define milestones and success criteria",
                "due_date": _due_in(3),
                "priority": "high",
                "estimated_time": 2.0,
            },
            {
                "title": "Collect key resources and links",
                "due_date": _due_in(5),
                "priority": "medium",
                "estimated_time": 1.5,
            },
            {
                "title": "Schedule the first work block",
                "due_date": _due_in(7),
                "priority": "medium",
                "estimated_time": 1.0,
            },
        ]

    # Clamp dates to avoid creating tasks earlier than today.
    @staticmethod
    def _clamp_date(target: date, earliest: date) -> date:
        return target if target >= earliest else earliest

    # Get an existing plan by goal ID
    def get_plan(self, goal_id: UUID) -> Optional[PlanResponse]:
        """
        Retrieve an existing plan from the database.
        """
        goal = self.goal_repo.get_goal(goal_id, include_children=True)
        if not goal:
            return None

        milestones = [
            PlanMilestone(
                id=str(milestone.id),
                title=milestone.title,
                target_date=milestone.target_date,
                definition_of_done=milestone.definition_of_done,
                order=milestone.order,
            )
            for milestone in goal.milestones
        ]
        tasks = [
            PlanTask(
                id=str(task.id),
                title=task.title,
                due_date=task.due_date,
                milestone_id=str(task.milestone_id),
                priority=task.priority,
                estimated_time=task.estimated_time,
            )
            for task in goal.tasks
        ]

        return PlanResponse(
            date=date.today(),
            focus=goal.title,
            milestones=milestones,
            tasks=tasks,
            artifacts=[],
            insights=None,
            resources=[],
            message=f"Plan for '{goal.title}' retrieved.",
            warnings=[],
        )

    # Update goal status
    def update_goal_status(self, goal_id: UUID, status: str) -> bool:
        """
        Update the status of a goal (e.g., 'in-progress', 'completed').
        """
        goal = self.goal_repo.get_goal(goal_id)
        if not goal:
            return False

        goal.status = status
        self.session.commit()
        return True

    # Get next actionable tasks
    def get_next_tasks(self, goal_id: UUID, limit: int = 5) -> List[PlanTask]:
        """
        Get the next actionable tasks for a goal, sorted by priority and due date.
        """
        goal = self.goal_repo.get_goal(goal_id, include_children=True)
        if not goal:
            return []

        # Filter incomplete tasks and sort by priority and due date
        incomplete_tasks = [
            task for task in goal.tasks
            if task.status != "completed"
        ]

        # Priority ranking
        priority_order = {"high": 0, "medium": 1, "low": 2}
        incomplete_tasks.sort(
            key=lambda t: (priority_order.get(t.priority, 3), t.due_date)
        )

        return [
            PlanTask(
                id=str(task.id),
                title=task.title,
                due_date=task.due_date,
                milestone_id=str(task.milestone_id),
                priority=task.priority,
                estimated_time=task.estimated_time,
            )
            for task in incomplete_tasks[:limit]
        ]
