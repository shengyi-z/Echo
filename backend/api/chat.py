"""
Chat API - Handle user messages and communicate with Backboard AI
"""
import os
import json
import re
from typing import Optional, Any, Dict, Tuple

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..init_echo import ensure_assistant, create_thread, send_message
from ..core.db import SessionLocal
from ..repo.goal_repo import GoalRepository

# Router config and Backboard base URL.
router = APIRouter(prefix="/api/chat", tags=["chat"])
BASE_URL = "https://app.backboard.io/api"


# =========================
# Pydantic Models
# =========================

class ChatRequest(BaseModel):
    message: str
    thread_id: str
    is_first_message: Optional[bool] = False


class ChatResponse(BaseModel):
    content: str
    thread_id: str
    role: str = "assistant"
    suggested_title: Optional[str] = None


class InitResponse(BaseModel):
    assistant_id: str
    thread_id: str
    message: str


class NewChatRequest(BaseModel):
    title: Optional[str] = None


class NewChatResponse(BaseModel):
    thread_id: str
    title: str
    created_at: str


class UpdateTitleRequest(BaseModel):
    thread_id: str
    title: str


class UpdateTitleResponse(BaseModel):
    success: bool
    thread_id: str
    title: str


# ============================================================
# ✅ C：用于“结构化 JSON 稳定提取 + 修复重试 + 类型归一化”的工具函数
# ============================================================

def _looks_like_plan_text(text: str) -> bool:
    """
    判断文本是否“像 planning JSON 输出”
    用于：解析失败时决定要不要自动重试一次
    """
    if not text:
        return False
    t = text.lower()
    keywords = [
        "```json",
        "milestones",
        "definition_of_done",
        "response_to_user",
        "goal_title",
        "resources",
        "insights",
        "\"goal\"",
    ]
    return any(k in t for k in keywords)


def _extract_json_from_fence(text: str) -> Optional[str]:
    """
    优先提取 ```json ... ``` 内的内容
    """
    if not text:
        return None
    m = re.search(r"```json\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    return m.group(1).strip() if m else None


def _extract_first_json_object(text: str) -> Optional[str]:
    """
    从全文中提取第一个“完整 JSON 对象”（用括号配对计数）
    解决：模型没用 ```json fence 或夹杂多余文本导致 parse 失败
    """
    if not text:
        return None

    s = text
    start = s.find("{")
    if start == -1:
        return None

    in_string = False
    escape = False
    depth = 0

    for i in range(start, len(s)):
        ch = s[i]

        if escape:
            escape = False
            continue

        if ch == "\\" and in_string:
            escape = True
            continue

        if ch == '"':
            in_string = not in_string
            continue

        if not in_string:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return s[start:i + 1].strip()

    # 没闭合：通常是模型输出被截断
    return None


def _try_parse_plan_json(content: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    尝试从 content 中解析出 plan JSON
    返回：(ok, parsed_dict_or_none, reason)
    """
    if not content:
        return False, None, "empty_content"

    # 1) 先从 fence 里拿
    candidate = _extract_json_from_fence(content)
    if candidate:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                # 只要具备 planning 的核心字段即可
                if "milestones" in parsed and "response_to_user" in parsed:
                    return True, parsed, "parsed_from_fence"
        except Exception:
            pass

    # 2) 再尝试从全文提取第一个完整 JSON 对象
    candidate = _extract_first_json_object(content)
    if candidate:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                if "milestones" in parsed and "response_to_user" in parsed:
                    return True, parsed, "parsed_from_text_object"
        except Exception:
            return False, None, "json_parse_failed"

    return False, None, "no_json_found_or_incomplete"


def _to_float_hours(value: Any) -> Optional[float]:
    """
    把 "8 hours" / "8h" / "2.5" / 8 等统一转 float
    避免你前端/DB 因类型不一致崩掉
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        m = re.search(r"(\d+(\.\d+)?)", value)
        if m:
            return float(m.group(1))
    return None


def _normalize_plan_types(plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    ✅ 把 plan JSON 里容易出问题的字段做“最小纠正”
    - estimated_time: 强制 float
    - priority: 非法值兜底为 medium
    """
    if not isinstance(plan, dict):
        return plan

    milestones = plan.get("milestones", [])
    if isinstance(milestones, list):
        for ms in milestones:
            if not isinstance(ms, dict):
                continue
            tasks = ms.get("tasks", [])
            if isinstance(tasks, list):
                for task in tasks:
                    if not isinstance(task, dict):
                        continue
                    task["estimated_time"] = _to_float_hours(task.get("estimated_time")) or 0.0
                    if task.get("priority") not in ("high", "medium", "low"):
                        task["priority"] = "medium"
    return plan


def _validate_dates(plan: Dict[str, Any]) -> Tuple[bool, list]:
    """
    验证plan中所有日期是否 >= 2026-01-14 (今天)
    返回: (is_valid, invalid_dates_list)
    """
    from datetime import datetime
    
    min_date = datetime(2026, 1, 14).date()
    invalid_dates = []
    
    # 检查goal.deadline
    if "goal" in plan and isinstance(plan["goal"], dict):
        deadline_str = plan["goal"].get("deadline")
        if deadline_str:
            try:
                deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
                if deadline < min_date:
                    invalid_dates.append(f"goal.deadline: {deadline_str}")
            except:
                pass
    
    # 检查所有milestone的target_date和task的due_date
    milestones = plan.get("milestones", [])
    if isinstance(milestones, list):
        for idx, ms in enumerate(milestones):
            if not isinstance(ms, dict):
                continue
            
            # 检查milestone target_date
            target_date_str = ms.get("target_date")
            if target_date_str:
                try:
                    target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
                    if target_date < min_date:
                        invalid_dates.append(f"milestone[{idx}].target_date: {target_date_str}")
                except:
                    pass
            
            # 检查tasks中的due_date
            tasks = ms.get("tasks", [])
            if isinstance(tasks, list):
                for task_idx, task in enumerate(tasks):
                    if not isinstance(task, dict):
                        continue
                    due_date_str = task.get("due_date")
                    if due_date_str:
                        try:
                            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                            if due_date < min_date:
                                invalid_dates.append(f"milestone[{idx}].task[{task_idx}].due_date: {due_date_str}")
                        except:
                            pass
    
    return len(invalid_dates) == 0, invalid_dates


def _date_validation_prompt(invalid_dates: list) -> str:
    """
    生成日期验证失败的修复提示
    """
    dates_str = "\n".join(f"  - {d}" for d in invalid_dates)
    return (
        f"ERROR: The following dates are BEFORE 2026-01-14 (today), which violates the requirement:\n"
        f"{dates_str}\n\n"
        f"CRITICAL: Today is 2026-01-14. ALL dates must be >= 2026-01-14.\n"
        f"Please regenerate the COMPLETE JSON with ALL dates corrected to be on or after 2026-01-14.\n"
        f"Output the full corrected JSON (wrapped in ```json fence), nothing else.\n"
    )


def _repair_prompt_v1() -> str:
    """
    第一次修复：要求严格 JSON + 修正 estimated_time 类型
    """
    return (
        "Your previous output is NOT valid/complete JSON (likely truncated or invalid).\n"
        "Re-output ONE valid JSON object ONLY (you may wrap with a single ```json fence). NO extra text.\n"
        "Include ALL required fields exactly: response_to_user, goal_title, milestones, insights, resources.\n"
        "IMPORTANT:\n"
        "- estimated_time must be a NUMBER (float hours), e.g. 8 or 2.5 (NOT '8 hours').\n"
        "- Keep it concise to avoid truncation.\n"
        "Now output the corrected JSON.\n"
    )


def _repair_prompt_v2_minimal() -> str:
    """
    第二次修复：要求“更短”的最小 JSON，避免再次被截断
    """
    return (
        "Still not parseable JSON.\n"
        "Now output a MINIMAL valid JSON object ONLY (you may wrap in ```json).\n"
        "Rules:\n"
        "- 3 milestones ONLY.\n"
        "- First 2 milestones: 5 tasks each.\n"
        "- Third milestone: 2 tasks.\n"
        "- resources: 3 items ONLY.\n"
        "- insights must be concise.\n"
        "- estimated_time must be NUMBER (float).\n"
        "Output JSON only, nothing else.\n"
    )


# =========================
# Routes
# =========================

@router.post("/init", response_model=InitResponse)
async def initialize_user():
    """
    用户登录时调用：确保助手存在 + 创建新对话线程
    """
    try:
        assistant_id = await ensure_assistant()
        thread_id = await create_thread(assistant_id)

        return InitResponse(
            assistant_id=assistant_id,
            thread_id=thread_id,
            message="✅ 初始化成功，可以开始对话了！"
        )
    except Exception as e:
        print(f"❌ 错误详情: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"初始化失败: {str(e)}")


@router.post("/new", response_model=NewChatResponse)
async def create_new_chat(request: NewChatRequest):
    """
    创建新的对话线程
    """
    try:
        assistant_id = await ensure_assistant()
        thread_id = await create_thread(assistant_id)

        from datetime import datetime
        title = request.title if request.title else "New Chat"

        return NewChatResponse(
            thread_id=str(thread_id),  # 转换 UUID 为字符串
            title=title,
            created_at=datetime.now().isoformat()
        )
    except Exception as e:
        print(f"❌ 错误详情: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"创建新对话失败: {str(e)}")


@router.post("/send", response_model=ChatResponse)
async def send_chat_message(request: ChatRequest):
    """
    发送用户消息到 Backboard AI 并返回回复
    如果是第一条消息，会根据内容生成建议的标题

    ✅ 关键增强：
    - 更稳的 JSON 提取（支持 fence + 括号配对）
    - 自动修复重试（最多 2 次）
    - estimated_time 类型归一化（"8 hours" -> 8.0）
    """
    if not request.thread_id:
        raise HTTPException(
            status_code=400,
            detail="请先调用 /api/chat/init 初始化对话"
        )

    try:
        # -------------------------
        # 1) 发送消息
        # -------------------------
        print(f"\n📤 发送消息到 thread_id: {request.thread_id}")
        print(f"📝 用户消息: {request.message}")
        print("=" * 80)

        content = await send_message(request.thread_id, request.message)

        print(f"\n🤖 AI 完整响应:\n{content}")
        print("=" * 80)

        # -------------------------
        # 2) 首条消息：生成标题（保留你原逻辑）
        # -------------------------
        suggested_title = None
        if request.is_first_message:
            suggested_title = await generate_chat_title_with_ai(request.message)

        # -------------------------
        # 3) 尝试解析 planning JSON（新增稳提取 + 自动修复）
        # -------------------------
        plan_data: Optional[Dict[str, Any]] = None
        ok, parsed, reason = _try_parse_plan_json(content)
        print(f"🔎 Plan JSON parse #1: ok={ok}, reason={reason}")

        if ok and isinstance(parsed, dict):
            plan_data = parsed
        else:
            # ✅ 如果看起来像 plan，但 JSON 不可解析，自动要求重输出一次（v1）
            if _looks_like_plan_text(content):
                print("♻️ 检测到疑似计划输出但 JSON 不可解析，自动重试 #2 (repair v1)...")
                content2 = await send_message(request.thread_id, _repair_prompt_v1())
                ok2, parsed2, reason2 = _try_parse_plan_json(content2)
                print(f"🔧 Plan JSON parse #2: ok={ok2}, reason={reason2}")
                if ok2 and isinstance(parsed2, dict):
                    content = content2
                    plan_data = parsed2
                else:
                    # ✅ 第二次还失败：再要求输出“更短的最小 JSON”（v2）
                    print("♻️ 仍不可解析，自动重试 #3 (repair v2 minimal)...")
                    content3 = await send_message(request.thread_id, _repair_prompt_v2_minimal())
                    ok3, parsed3, reason3 = _try_parse_plan_json(content3)
                    print(f"🔧 Plan JSON parse #3: ok={ok3}, reason={reason3}")
                    if ok3 and isinstance(parsed3, dict):
                        content = content3
                        plan_data = parsed3

        # -------------------------
        # 4) 如果解析成功：做类型归一化 + 日期验证
        # -------------------------
        if plan_data is not None:
            plan_data = _normalize_plan_types(plan_data)
            
            # ✅ 日期验证：检查所有日期是否 >= 2026-01-14
            is_valid, invalid_dates = _validate_dates(plan_data)
            if not is_valid:
                print(f"⚠️ 检测到无效日期（早于2026-01-14）: {invalid_dates}")
                print("♻️ 自动要求AI修正日期...")
                
                # 要求AI重新生成，修正日期
                date_fix_content = await send_message(request.thread_id, _date_validation_prompt(invalid_dates))
                ok_fixed, parsed_fixed, reason_fixed = _try_parse_plan_json(date_fix_content)
                print(f"🔧 Date fix parse: ok={ok_fixed}, reason={reason_fixed}")
                
                if ok_fixed and isinstance(parsed_fixed, dict):
                    # 再次验证修正后的日期
                    is_valid_fixed, invalid_dates_fixed = _validate_dates(parsed_fixed)
                    if is_valid_fixed:
                        print("✅ 日期已修正")
                        content = date_fix_content
                        plan_data = _normalize_plan_types(parsed_fixed)
                    else:
                        print(f"⚠️ 修正后仍有无效日期: {invalid_dates_fixed}")
                        # 仍然使用修正后的数据，但记录警告
                        content = date_fix_content
                        plan_data = _normalize_plan_types(parsed_fixed)

            # ✅ 回写为标准 JSON fence（前端 regex/parse 更稳定）
            # 说明：即使模型原来没有 fence，这里也会统一包装一次，减少前端分支
            content = "```json\n" + json.dumps(plan_data, ensure_ascii=False, indent=2) + "\n```"

        # -------------------------
        # 5) DB 存储（保留你原逻辑：只存旧 schema 的 goal）
        #    你当前 DB create_goal() deadline 是必填 date，所以不能乱存
        # -------------------------
        try:
            if plan_data and isinstance(plan_data, dict) and "goal" in plan_data:
                print(f"\n📊 检测到 planning(旧schema: goal) 格式，正在存储到数据库...")

                session = SessionLocal()
                try:
                    goal_repo = GoalRepository(session)

                    goal_info = plan_data["goal"]
                    milestones_data = plan_data.get("milestones", [])

                    # 转换 milestones 格式
                    milestones_payload = []
                    for milestone in milestones_data:
                        tasks = milestone.get("tasks", []) if isinstance(milestone, dict) else []
                        milestone_payload = {
                            "title": milestone.get("title") if isinstance(milestone, dict) else None,
                            "target_date": milestone.get("target_date") if isinstance(milestone, dict) else None,
                            "definition_of_done": milestone.get("definition_of_done") if isinstance(milestone, dict) else None,
                            "order": milestone.get("order") if isinstance(milestone, dict) else None,
                            "status": "not-started",
                            "tasks": [
                                {
                                    "title": task.get("title"),
                                    "due_date": task.get("due_date"),
                                    "priority": task.get("priority", "medium"),
                                    "estimated_time": task.get("estimated_time", 1.0),
                                }
                                for task in tasks if isinstance(task, dict)
                            ]
                        }
                        milestones_payload.append(milestone_payload)

                    # 创建 goal（注意：deadline 必须存在，否则 create_goal 会报错）
                    goal = goal_repo.create_goal(
                        memory_id=request.thread_id,
                        title=goal_info.get("title"),
                        type=goal_info.get("type", "General"),
                        deadline=goal_info.get("deadline"),
                        status="not-started",
                        milestones=milestones_payload
                    )
                    session.commit()

                    print(f"✅ Goal已存储: {goal.title} (ID: {goal.id})")
                    print(f"   包含 {len(milestones_payload)} 个 milestones")

                except Exception as e:
                    print(f"⚠️ 存储goal失败: {e}")
                    session.rollback()
                finally:
                    session.close()

        except Exception:
            # 任何 DB 存储异常都不影响 chat 返回
            print("💬 普通聊天响应（或新schema未入库），继续返回给前端。")
            pass

        # -------------------------
        # 6) 返回给前端
        # -------------------------
        return ChatResponse(
            content=content,
            thread_id=request.thread_id,
            role="assistant",
            suggested_title=suggested_title
        )

    except Exception as e:
        print(f"❌ 错误详情: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"发送消息失败: {str(e)}")


@router.post("/update-title", response_model=UpdateTitleResponse)
async def update_chat_title(request: UpdateTitleRequest):
    """
    更新对话标题
    """
    try:
        return UpdateTitleResponse(
            success=True,
            thread_id=request.thread_id,
            title=request.title
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新标题失败: {str(e)}")


# ============================================================
# ✅ 你原本的“AI 自动生成标题”逻辑（保留不改）
# ============================================================

async def generate_chat_title_with_ai(user_message: str) -> str:
    """
    使用 AI 根据用户第一条消息生成简短的对话标题
    """
    try:
        api_key = os.getenv("BACKBOARD_API_KEY")
        assistant_id = os.getenv("BACKBOARD_ASSISTANT_ID")

        if not api_key or not assistant_id:
            return generate_simple_title(user_message)

        # 创建临时线程用于生成标题
        headers = {"X-API-Key": api_key}
        response = requests.post(
            f"{BASE_URL}/assistants/{assistant_id}/threads",
            json={},
            headers=headers
        )
        response.raise_for_status()
        temp_thread_id = response.json()["thread_id"]

        # 请求 AI 生成标题
        prompt = f"""Based on this user message, generate a short, descriptive chat title (3-5 words max, no quotes):

User message: "{user_message}"

Reply with ONLY the title, nothing else."""

        payload = {
            "content": prompt,
            "memory": "Off",
            "web_search": "Off",
            "stream": "false"
        }

        response = requests.post(
            f"{BASE_URL}/threads/{temp_thread_id}/messages",
            data=payload,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()

        title = response.json().get("content", "").strip()

        # 清理标题（移除引号等）
        title = title.replace('"', '').replace("'", '').strip()

        # 如果标题太长或为空，使用简单方法
        if len(title) > 40 or len(title) < 3:
            return generate_simple_title(user_message)

        return title

    except Exception as e:
        print(f"AI title generation failed: {e}")
        return generate_simple_title(user_message)


def generate_simple_title(user_message: str) -> str:
    """
    备用方案：简单的标题生成
    """
    words = user_message.split()[:5]
    title = ' '.join(words)
    if len(title) > 30:
        title = title[:27] + "..."
    return title if title else "New Chat"
