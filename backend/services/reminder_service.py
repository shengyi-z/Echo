from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models.reminder import Reminder, ReminderType, ReminderPriority
from ..models.goal import Goal
from ..models.milestone import Milestone
from ..models.task import Task
from ..repo.goal_repo import GoalRepository
from .chat_service import ChatService


class ReminderService:
    """
    智能提醒服务
    - 自动创建基于任务/里程碑的提醒
    - 每日简报和周度总结
    - AI 辅助的智能提醒内容生成
    - 提醒优先级管理
    """

    def __init__(self, session: Session):
        self.session = session
        self.goal_repo = GoalRepository(session)
        self.chat_service = ChatService()

    # ==================== 提醒 CRUD 操作 ====================

    def create_reminder(
        self,
        title: str,
        message: str,
        remind_at: datetime,
        type: ReminderType = ReminderType.CUSTOM,
        priority: ReminderPriority = ReminderPriority.MEDIUM,
        goal_id: Optional[UUID] = None,
        milestone_id: Optional[UUID] = None,
        task_id: Optional[UUID] = None,
    ) -> Reminder:
        """
        创建新提醒
        """
        reminder = Reminder(
            type=type,
            priority=priority,
            title=title,
            message=message,
            remind_at=remind_at,
            goal_id=str(goal_id) if goal_id else None,
            milestone_id=str(milestone_id) if milestone_id else None,
            task_id=str(task_id) if task_id else None,
        )

        self.session.add(reminder)
        self.session.commit()
        self.session.refresh(reminder)

        return reminder

    def get_reminder(self, reminder_id: str) -> Optional[Reminder]:
        """获取特定提醒"""
        return self.session.query(Reminder).filter(
            Reminder.id == reminder_id
        ).first()

    def get_pending_reminders(
        self,
        before: Optional[datetime] = None,
        limit: int = 50
    ) -> List[Reminder]:
        """
        获取待处理的提醒（未读且未完成）

        Args:
            before: 获取此时间之前的提醒（默认当前时间）
            limit: 最大返回数量
        """
        if before is None:
            before = datetime.utcnow()

        reminders = self.session.query(Reminder).filter(
            and_(
                Reminder.remind_at <= before,
                Reminder.is_completed == False,
                Reminder.is_dismissed == False
            )
        ).order_by(
            Reminder.priority.desc(),
            Reminder.remind_at.asc()
        ).limit(limit).all()

        return reminders

    def get_upcoming_reminders(
        self,
        hours_ahead: int = 24,
        limit: int = 20
    ) -> List[Reminder]:
        """
        获取即将到来的提醒（未来 N 小时内）
        """
        now = datetime.utcnow()
        future = now + timedelta(hours=hours_ahead)

        reminders = self.session.query(Reminder).filter(
            and_(
                Reminder.remind_at.between(now, future),
                Reminder.is_completed == False,
                Reminder.is_dismissed == False
            )
        ).order_by(
            Reminder.remind_at.asc()
        ).limit(limit).all()

        return reminders

    def mark_as_read(self, reminder_id: str) -> bool:
        """标记提醒为已读"""
        reminder = self.get_reminder(reminder_id)
        if not reminder:
            return False

        reminder.is_read = True
        self.session.commit()
        return True

    def mark_as_completed(self, reminder_id: str) -> bool:
        """标记提醒为已完成"""
        reminder = self.get_reminder(reminder_id)
        if not reminder:
            return False

        reminder.is_completed = True
        reminder.is_read = True
        self.session.commit()
        return True

    def dismiss_reminder(self, reminder_id: str) -> bool:
        """忽略/取消提醒"""
        reminder = self.get_reminder(reminder_id)
        if not reminder:
            return False

        reminder.is_dismissed = True
        self.session.commit()
        return True

    def delete_reminder(self, reminder_id: str) -> bool:
        """删除提醒"""
        reminder = self.get_reminder(reminder_id)
        if not reminder:
            return False

        self.session.delete(reminder)
        self.session.commit()
        return True

    # ==================== 自动提醒生成 ====================

    def generate_task_reminders(
        self,
        task_id: UUID,
        advance_days: List[int] = [1, 3, 7]
    ) -> List[Reminder]:
        """
        为任务自动创建提前提醒

        Args:
            task_id: 任务 ID
            advance_days: 提前几天提醒（默认：1天、3天、7天前）

        Returns:
            创建的提醒列表
        """
        task = self.session.query(Task).filter(Task.id == task_id).first()
        if not task or not task.due_date:
            return []

        reminders = []
        due_datetime = datetime.combine(task.due_date, datetime.min.time())

        for days in advance_days:
            remind_at = due_datetime - timedelta(days=days)

            # 不创建过去的提醒
            if remind_at < datetime.utcnow():
                continue

            # 检查是否已存在相同的提醒
            existing = self.session.query(Reminder).filter(
                and_(
                    Reminder.task_id == str(task_id),
                    Reminder.type == ReminderType.TASK_DUE,
                    Reminder.remind_at == remind_at
                )
            ).first()

            if existing:
                continue

            # 确定优先级
            if days == 1:
                priority = ReminderPriority.URGENT
            elif days <= 3:
                priority = ReminderPriority.HIGH
            else:
                priority = ReminderPriority.MEDIUM

            reminder = self.create_reminder(
                title=f"任务即将到期: {task.title}",
                message=f"任务「{task.title}」将在 {days} 天后到期（{task.due_date.strftime('%Y-%m-%d')}）",
                remind_at=remind_at,
                type=ReminderType.TASK_DUE,
                priority=priority,
                goal_id=task.goal_id,
                task_id=task_id
            )
            reminders.append(reminder)

        return reminders

    def generate_milestone_reminders(
        self,
        milestone_id: UUID,
        advance_days: List[int] = [3, 7, 14]
    ) -> List[Reminder]:
        """
        为里程碑创建提前提醒
        """
        milestone = self.session.query(Milestone).filter(
            Milestone.id == milestone_id
        ).first()

        if not milestone or not milestone.target_date:
            return []

        reminders = []
        target_datetime = datetime.combine(
            milestone.target_date, datetime.min.time())

        for days in advance_days:
            remind_at = target_datetime - timedelta(days=days)

            if remind_at < datetime.utcnow():
                continue

            existing = self.session.query(Reminder).filter(
                and_(
                    Reminder.milestone_id == str(milestone_id),
                    Reminder.type == ReminderType.MILESTONE_DUE,
                    Reminder.remind_at == remind_at
                )
            ).first()

            if existing:
                continue

            if days <= 3:
                priority = ReminderPriority.URGENT
            elif days <= 7:
                priority = ReminderPriority.HIGH
            else:
                priority = ReminderPriority.MEDIUM

            reminder = self.create_reminder(
                title=f"里程碑即将到期: {milestone.title}",
                message=f"里程碑「{milestone.title}」将在 {days} 天后到期（{milestone.target_date.strftime('%Y-%m-%d')}）",
                remind_at=remind_at,
                type=ReminderType.MILESTONE_DUE,
                priority=priority,
                goal_id=milestone.goal_id,
                milestone_id=milestone_id
            )
            reminders.append(reminder)

        return reminders

    def generate_goal_deadline_reminders(
        self,
        goal_id: UUID,
        advance_days: List[int] = [7, 14, 30]
    ) -> List[Reminder]:
        """
        为目标截止日期创建提醒
        """
        goal = self.goal_repo.get_goal(goal_id)
        if not goal or not goal.deadline:
            return []

        reminders = []
        deadline_datetime = datetime.combine(
            goal.deadline, datetime.min.time())

        for days in advance_days:
            remind_at = deadline_datetime - timedelta(days=days)

            if remind_at < datetime.utcnow():
                continue

            existing = self.session.query(Reminder).filter(
                and_(
                    Reminder.goal_id == str(goal_id),
                    Reminder.type == ReminderType.GOAL_DEADLINE,
                    Reminder.remind_at == remind_at
                )
            ).first()

            if existing:
                continue

            if days <= 7:
                priority = ReminderPriority.URGENT
            elif days <= 14:
                priority = ReminderPriority.HIGH
            else:
                priority = ReminderPriority.MEDIUM

            reminder = self.create_reminder(
                title=f"目标截止日期临近: {goal.title}",
                message=f"目标「{goal.title}」将在 {days} 天后到期（{goal.deadline.strftime('%Y-%m-%d')}）",
                remind_at=remind_at,
                type=ReminderType.GOAL_DEADLINE,
                priority=priority,
                goal_id=goal_id
            )
            reminders.append(reminder)

        return reminders

    def auto_generate_reminders_for_goal(self, goal_id: UUID) -> Dict[str, List[Reminder]]:
        """
        为目标自动生成所有相关提醒（目标、里程碑、任务）
        """
        goal = self.goal_repo.get_goal(goal_id, include_children=True)
        if not goal:
            return {}

        result = {
            "goal_reminders": [],
            "milestone_reminders": [],
            "task_reminders": []
        }

        # 目标截止日期提醒
        result["goal_reminders"] = self.generate_goal_deadline_reminders(
            goal_id)

        # 里程碑提醒
        for milestone in goal.milestones:
            reminders = self.generate_milestone_reminders(milestone.id)
            result["milestone_reminders"].extend(reminders)

        # 任务提醒
        for task in goal.tasks:
            reminders = self.generate_task_reminders(task.id)
            result["task_reminders"].extend(reminders)

        return result

    # ==================== 每日简报和周度总结 ====================

    async def generate_daily_briefing(
        self,
        thread_id: str,
        target_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        生成每日简报

        包含：
        - 今日到期的任务
        - 即将到来的里程碑
        - 逾期项目
        - AI 生成的每日建议
        """
        if target_date is None:
            target_date = date.today()

        # 获取今日到期的任务
        today_tasks = self.session.query(Task).filter(
            and_(
                Task.due_date == target_date,
                Task.status != "completed"
            )
        ).all()

        # 获取本周到期的里程碑
        week_end = target_date + timedelta(days=7)
        upcoming_milestones = self.session.query(Milestone).filter(
            and_(
                Milestone.target_date.between(target_date, week_end),
                Milestone.status != "completed"
            )
        ).all()

        # 获取逾期任务
        overdue_tasks = self.session.query(Task).filter(
            and_(
                Task.due_date < target_date,
                Task.status != "completed"
            )
        ).all()

        briefing = {
            "date": target_date.isoformat(),
            "today_tasks": [
                {
                    "id": str(task.id),
                    "title": task.title,
                    "priority": task.priority,
                    "estimated_time": task.estimated_time
                }
                for task in today_tasks
            ],
            "upcoming_milestones": [
                {
                    "id": str(milestone.id),
                    "title": milestone.title,
                    "target_date": milestone.target_date.isoformat(),
                    "days_until": (milestone.target_date - target_date).days
                }
                for milestone in upcoming_milestones
            ],
            "overdue_tasks": [
                {
                    "id": str(task.id),
                    "title": task.title,
                    "days_overdue": (target_date - task.due_date).days
                }
                for task in overdue_tasks
            ],
        }

        # 使用 AI 生成每日建议
        ai_briefing = await self._generate_ai_daily_briefing(briefing, thread_id)
        briefing["ai_summary"] = ai_briefing

        return briefing

    async def generate_weekly_summary(
        self,
        thread_id: str,
        week_start: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        生成周度总结

        包含：
        - 本周完成的任务统计
        - 本周完成的里程碑
        - 下周的重点任务
        - AI 生成的周度分析
        """
        if week_start is None:
            # 默认从本周一开始
            today = date.today()
            week_start = today - timedelta(days=today.weekday())

        week_end = week_start + timedelta(days=6)

        # 本周完成的任务
        completed_tasks = self.session.query(Task).filter(
            and_(
                Task.status == "completed",
                Task.due_date.between(week_start, week_end)
            )
        ).all()

        # 本周完成的里程碑
        completed_milestones = self.session.query(Milestone).filter(
            and_(
                Milestone.status == "completed",
                Milestone.target_date.between(week_start, week_end)
            )
        ).all()

        # 下周的重点任务
        next_week_start = week_end + timedelta(days=1)
        next_week_end = next_week_start + timedelta(days=6)

        next_week_tasks = self.session.query(Task).filter(
            and_(
                Task.due_date.between(next_week_start, next_week_end),
                Task.status != "completed",
                or_(
                    Task.priority == "high",
                    Task.priority == "urgent"
                )
            )
        ).order_by(Task.due_date.asc()).all()

        summary = {
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "completed_tasks_count": len(completed_tasks),
            "completed_milestones_count": len(completed_milestones),
            "completed_tasks": [
                {
                    "id": str(task.id),
                    "title": task.title,
                    "completed_date": task.due_date.isoformat() if task.due_date else None
                }
                for task in completed_tasks
            ],
            "completed_milestones": [
                {
                    "id": str(milestone.id),
                    "title": milestone.title,
                    "completed_date": milestone.target_date.isoformat() if milestone.target_date else None
                }
                for milestone in completed_milestones
            ],
            "next_week_priorities": [
                {
                    "id": str(task.id),
                    "title": task.title,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "priority": task.priority
                }
                for task in next_week_tasks[:10]  # 最多显示 10 个
            ]
        }

        # AI 生成周度分析
        ai_summary = await self._generate_ai_weekly_summary(summary, thread_id)
        summary["ai_analysis"] = ai_summary

        return summary

    def schedule_daily_briefing(self, remind_time: datetime) -> Reminder:
        """
        安排每日简报提醒
        """
        return self.create_reminder(
            title="📅 每日简报",
            message="查看今日任务和重要事项",
            remind_at=remind_time,
            type=ReminderType.DAILY_BRIEFING,
            priority=ReminderPriority.HIGH
        )

    def schedule_weekly_summary(self, remind_time: datetime) -> Reminder:
        """
        安排周度总结提醒
        """
        return self.create_reminder(
            title="📊 周度总结",
            message="查看本周进展和下周计划",
            remind_at=remind_time,
            type=ReminderType.WEEKLY_SUMMARY,
            priority=ReminderPriority.MEDIUM
        )

    # ==================== 智能提醒内容生成 ====================

    async def generate_smart_reminder_message(
        self,
        task_id: UUID,
        thread_id: str
    ) -> str:
        """
        使用 AI 生成智能提醒消息（包含上下文和建议）
        """
        task = self.session.query(Task).filter(Task.id == task_id).first()
        if not task:
            return "任务不存在"

        goal = self.goal_repo.get_goal(task.goal_id) if task.goal_id else None

        prompt = f"""
请为以下任务生成一条友好、激励性的提醒消息：

**任务信息：**
- 标题：{task.title}
- 描述：{task.description if hasattr(task, 'description') else '无'}
- 优先级：{task.priority}
- 预计用时：{task.estimated_time} 小时
- 截止日期：{task.due_date.strftime('%Y-%m-%d') if task.due_date else '无'}

{"**所属目标：**" + goal.title if goal else ""}

请生成：
1. 一条简短、积极的提醒语（50字以内）
2. 一个可执行的建议（如何开始这个任务）

格式：
提醒：[你的提醒语]
建议：[你的建议]
"""

        try:
            response = await self.chat_service.send_message(
                content=prompt,
                thread_id=thread_id,
                memory="Auto"
            )
            return response
        except Exception as e:
            print(f"❌ AI 提醒生成失败: {e}")
            return f"记得完成任务：{task.title}"

    # ==================== 私有辅助方法 ====================

    async def _generate_ai_daily_briefing(
        self,
        briefing: Dict[str, Any],
        thread_id: str
    ) -> str:
        """使用 AI 生成每日简报总结"""
        prompt = f"""
请为用户生成今日工作简报：

**今日任务（{len(briefing['today_tasks'])} 个）：**
{self._format_tasks_for_ai(briefing['today_tasks'])}

**即将到来的里程碑（{len(briefing['upcoming_milestones'])} 个）：**
{self._format_milestones_for_ai(briefing['upcoming_milestones'])}

**逾期任务（{len(briefing['overdue_tasks'])} 个）：**
{self._format_overdue_for_ai(briefing['overdue_tasks'])}

请提供：
1. **今日重点**：应该优先完成什么？
2. **时间建议**：如何合理安排今天的时间？
3. **激励语**：一句积极的鼓励

保持简洁、友好、可执行。
"""

        try:
            response = await self.chat_service.send_message(
                content=prompt,
                thread_id=thread_id,
                memory="Auto"
            )
            return response
        except Exception as e:
            print(f"❌ AI 简报生成失败: {e}")
            return "今天也要加油哦！"

    async def _generate_ai_weekly_summary(
        self,
        summary: Dict[str, Any],
        thread_id: str
    ) -> str:
        """使用 AI 生成周度总结"""
        prompt = f"""
请为用户生成本周工作总结：

**本周完成：**
- 任务：{summary['completed_tasks_count']} 个
- 里程碑：{summary['completed_milestones_count']} 个

**下周重点任务（{len(summary['next_week_priorities'])} 个）：**
{self._format_tasks_for_ai(summary['next_week_priorities'])}

请提供：
1. **本周亮点**：值得庆祝的成就
2. **下周规划**：如何安排下周的工作？
3. **建议**：有什么可以改进的地方？

保持积极、鼓舞人心。
"""

        try:
            response = await self.chat_service.send_message(
                content=prompt,
                thread_id=thread_id,
                memory="Auto"
            )
            return response
        except Exception as e:
            print(f"❌ AI 总结生成失败: {e}")
            return "本周辛苦了，下周继续努力！"

    def _format_tasks_for_ai(self, tasks: List[Dict[str, Any]]) -> str:
        """格式化任务列表用于 AI 提示"""
        if not tasks:
            return "无"

        formatted = []
        for task in tasks[:5]:  # 最多显示 5 个
            formatted.append(f"- {task['title']}")
        return "\n".join(formatted)

    def _format_milestones_for_ai(self, milestones: List[Dict[str, Any]]) -> str:
        """格式化里程碑列表用于 AI 提示"""
        if not milestones:
            return "无"

        formatted = []
        for milestone in milestones:
            formatted.append(
                f"- {milestone['title']} ({milestone['days_until']} 天后)"
            )
        return "\n".join(formatted)

    def _format_overdue_for_ai(self, overdue: List[Dict[str, Any]]) -> str:
        """格式化逾期任务列表用于 AI 提示"""
        if not overdue:
            return "无"

        formatted = []
        for task in overdue[:5]:
            formatted.append(
                f"- {task['title']} (逾期 {task['days_overdue']} 天)"
            )
        return "\n".join(formatted)
