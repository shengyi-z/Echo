"""
ProgressService - 提供目标、里程碑和任务的进度跟踪和分析功能
"""
from datetime import date, timedelta
from typing import Dict, List, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from ..repo.goal_repo import GoalRepository
from ..models.goal import Goal
from ..models.milestone import Milestone
from ..models.task import Task
from .chat_service import ChatService


class ProgressService:
    """
    进度跟踪服务
    - 计算目标完成进度
    - 识别阻塞和风险
    - 生成进度报告
    - AI 辅助的进度分析和建议
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.goal_repo = GoalRepository(session)
        self.chat_service = ChatService()
    
    # ==================== 核心进度计算 ====================
    
    def calculate_progress(self, goal_id: UUID) -> Dict[str, Any]:
        """
        计算目标的完成进度统计
        
        Returns:
            {
                "goal_id": str,
                "goal_title": str,
                "milestone_progress": float,  # 里程碑完成百分比
                "task_progress": float,       # 任务完成百分比
                "overall_progress": float,    # 综合进度
                "completed_milestones": int,
                "total_milestones": int,
                "completed_tasks": int,
                "total_tasks": int,
                "days_remaining": int,
                "status": str,
                "on_track": bool,            # 是否按计划进行
                "time_health": str           # "healthy", "warning", "critical"
            }
        """
        goal = self.goal_repo.get_goal(goal_id, include_children=True)
        if not goal:
            return {}
        
        total_milestones = len(goal.milestones)
        completed_milestones = sum(
            1 for m in goal.milestones if m.status == "completed"
        )
        
        total_tasks = len(goal.tasks)
        completed_tasks = sum(
            1 for t in goal.tasks if t.status == "completed"
        )
        
        milestone_progress = (
            (completed_milestones / total_milestones * 100) 
            if total_milestones > 0 else 0
        )
        task_progress = (
            (completed_tasks / total_tasks * 100) 
            if total_tasks > 0 else 0
        )
        
        today = date.today()
        days_remaining = (goal.deadline - today).days if goal.deadline else None
        
        # 计算时间健康度
        time_health = self._calculate_time_health(
            overall_progress=(milestone_progress + task_progress) / 2,
            days_remaining=days_remaining,
            goal=goal
        )
        
        # 判断是否按计划进行
        on_track = self._is_on_track(
            completed_tasks=completed_tasks,
            total_tasks=total_tasks,
            days_remaining=days_remaining,
            goal=goal
        )
        
        return {
            "goal_id": str(goal.id),
            "goal_title": goal.title,
            "milestone_progress": round(milestone_progress, 1),
            "task_progress": round(task_progress, 1),
            "overall_progress": round((milestone_progress + task_progress) / 2, 1),
            "completed_milestones": completed_milestones,
            "total_milestones": total_milestones,
            "completed_tasks": completed_tasks,
            "total_tasks": total_tasks,
            "days_remaining": days_remaining,
            "status": goal.status,
            "on_track": on_track,
            "time_health": time_health,
        }
    
    def get_milestone_progress(self, milestone_id: UUID) -> Dict[str, Any]:
        """
        获取特定里程碑的进度
        """
        milestone = self.session.query(Milestone).filter(
            Milestone.id == milestone_id
        ).first()
        
        if not milestone:
            return {}
        
        # 获取该里程碑下的所有任务
        tasks = self.session.query(Task).filter(
            Task.milestone_id == milestone_id
        ).all()
        
        total_tasks = len(tasks)
        completed_tasks = sum(1 for t in tasks if t.status == "completed")
        in_progress_tasks = sum(1 for t in tasks if t.status == "in_progress")
        
        progress_percentage = (
            (completed_tasks / total_tasks * 100) 
            if total_tasks > 0 else 0
        )
        
        return {
            "milestone_id": str(milestone.id),
            "milestone_title": milestone.title,
            "status": milestone.status,
            "progress_percentage": round(progress_percentage, 1),
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "total_tasks": total_tasks,
            "target_date": milestone.target_date.isoformat() if milestone.target_date else None,
            "is_overdue": milestone.target_date < date.today() if milestone.target_date else False,
        }
    
    # ==================== 阻塞和风险识别 ====================
    
    def identify_blockers(self, goal_id: UUID) -> List[Dict[str, Any]]:
        """
        识别目标中的阻塞因素
        - 逾期的任务
        - 长时间未更新的任务
        - 依赖关系导致的阻塞
        """
        goal = self.goal_repo.get_goal(goal_id, include_children=True)
        if not goal:
            return []
        
        blockers = []
        today = date.today()
        
        for task in goal.tasks:
            # 逾期任务
            if task.due_date and task.due_date < today and task.status != "completed":
                blockers.append({
                    "type": "overdue_task",
                    "severity": "high",
                    "task_id": str(task.id),
                    "task_title": task.title,
                    "days_overdue": (today - task.due_date).days,
                    "message": f"任务 '{task.title}' 已逾期 {(today - task.due_date).days} 天"
                })
            
            # 即将到期的高优先级任务
            elif task.due_date and task.priority == "high" and task.status != "completed":
                days_until_due = (task.due_date - today).days
                if 0 <= days_until_due <= 3:
                    blockers.append({
                        "type": "urgent_task",
                        "severity": "medium",
                        "task_id": str(task.id),
                        "task_title": task.title,
                        "days_until_due": days_until_due,
                        "message": f"高优先级任务 '{task.title}' 将在 {days_until_due} 天后到期"
                    })
        
        # 检查逾期的里程碑
        for milestone in goal.milestones:
            if milestone.target_date and milestone.target_date < today and milestone.status != "completed":
                blockers.append({
                    "type": "overdue_milestone",
                    "severity": "critical",
                    "milestone_id": str(milestone.id),
                    "milestone_title": milestone.title,
                    "days_overdue": (today - milestone.target_date).days,
                    "message": f"里程碑 '{milestone.title}' 已逾期 {(today - milestone.target_date).days} 天"
                })
        
        return sorted(blockers, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}[x["severity"]])
    
    def get_at_risk_goals(self) -> List[Dict[str, Any]]:
        """
        获取所有有风险的目标（进度落后或即将逾期）
        """
        # 获取进行中和未开始的目标
        in_progress_goals = self.goal_repo.list_goals(status="in_progress")
        not_started_goals = self.goal_repo.list_goals(status="not_started")
        goals = in_progress_goals + not_started_goals
        
        at_risk = []
        
        for goal in goals:
            progress = self.calculate_progress(goal.id)
            
            # 风险评估标准
            is_at_risk = False
            risk_factors = []
            
            # 1. 进度落后
            if progress["overall_progress"] < 50 and progress["days_remaining"] and progress["days_remaining"] < 30:
                is_at_risk = True
                risk_factors.append("进度落后于时间")
            
            # 2. 即将截止
            if progress["days_remaining"] and progress["days_remaining"] < 7:
                is_at_risk = True
                risk_factors.append(f"距离截止日期仅剩 {progress['days_remaining']} 天")
            
            # 3. 逾期
            if progress["days_remaining"] and progress["days_remaining"] < 0:
                is_at_risk = True
                risk_factors.append("已逾期")
            
            if is_at_risk:
                at_risk.append({
                    "goal_id": str(goal.id),
                    "goal_title": goal.title,
                    "progress": progress["overall_progress"],
                    "days_remaining": progress["days_remaining"],
                    "risk_factors": risk_factors,
                    "time_health": progress["time_health"],
                })
        
        return at_risk
    
    # ==================== 进度报告生成 ====================
    
    async def generate_progress_report(
        self, 
        goal_id: UUID, 
        thread_id: str,
        include_ai_insights: bool = True
    ) -> Dict[str, Any]:
        """
        生成目标的综合进度报告
        
        Args:
            goal_id: 目标 ID
            thread_id: Backboard 线程 ID
            include_ai_insights: 是否包含 AI 分析和建议
        
        Returns:
            完整的进度报告，包含统计、阻塞因素、AI 建议等
        """
        goal = self.goal_repo.get_goal(goal_id, include_children=True)
        if not goal:
            return {"error": "Goal not found"}
        
        # 1. 基础进度数据
        progress = self.calculate_progress(goal_id)
        
        # 2. 阻塞因素
        blockers = self.identify_blockers(goal_id)
        
        # 3. 里程碑进度
        milestone_details = [
            self.get_milestone_progress(m.id) 
            for m in goal.milestones
        ]
        
        # 4. 即将到期的任务
        upcoming_tasks = self._get_upcoming_tasks(goal)
        
        report = {
            "goal": {
                "id": str(goal.id),
                "title": goal.title,
                "type": goal.type,
                "status": goal.status,
                "deadline": goal.deadline.isoformat() if goal.deadline else None,
            },
            "progress": progress,
            "milestones": milestone_details,
            "blockers": blockers,
            "upcoming_tasks": upcoming_tasks,
            "generated_at": date.today().isoformat(),
        }
        
        # 5. AI 分析和建议（可选）
        if include_ai_insights:
            ai_insights = await self._generate_ai_insights(goal, progress, blockers, thread_id)
            report["ai_insights"] = ai_insights
        
        return report
    
    async def generate_weekly_summary(
        self, 
        thread_id: str,
        user_timezone: str = "UTC"
    ) -> Dict[str, Any]:
        """
        生成用户所有目标的周度总结
        """
        # 获取所有活跃目标
        active_goals = self.goal_repo.list_goals(status_filter=["in_progress"])
        
        summary = {
            "period": "week",
            "generated_at": date.today().isoformat(),
            "total_active_goals": len(active_goals),
            "goals": [],
            "overall_health": "healthy",
        }
        
        critical_count = 0
        warning_count = 0
        
        for goal in active_goals:
            progress = self.calculate_progress(goal.id)
            blockers = self.identify_blockers(goal.id)
            
            goal_summary = {
                "goal_id": str(goal.id),
                "title": goal.title,
                "progress": progress["overall_progress"],
                "time_health": progress["time_health"],
                "blocker_count": len(blockers),
            }
            
            summary["goals"].append(goal_summary)
            
            if progress["time_health"] == "critical":
                critical_count += 1
            elif progress["time_health"] == "warning":
                warning_count += 1
        
        # 整体健康度评估
        if critical_count > 0:
            summary["overall_health"] = "critical"
        elif warning_count > 0:
            summary["overall_health"] = "warning"
        
        # AI 生成周度建议
        ai_summary = await self._generate_weekly_ai_summary(summary, thread_id)
        summary["ai_summary"] = ai_summary
        
        return summary
    
    # ==================== 私有辅助方法 ====================
    
    def _calculate_time_health(
        self, 
        overall_progress: float, 
        days_remaining: Optional[int],
        goal: Goal
    ) -> str:
        """
        计算时间健康度
        """
        if not days_remaining:
            return "unknown"
        
        if days_remaining < 0:
            return "critical"  # 已逾期
        
        # 计算理想进度（基于时间流逝）
        if goal.deadline:
            total_days = (goal.deadline - goal.created_at.date()).days if hasattr(goal, 'created_at') else 90
            days_elapsed = total_days - days_remaining
            expected_progress = (days_elapsed / total_days * 100) if total_days > 0 else 0
            
            progress_gap = overall_progress - expected_progress
            
            if progress_gap < -20:
                return "critical"  # 进度远落后于时间
            elif progress_gap < -10:
                return "warning"   # 进度略微落后
            else:
                return "healthy"   # 进度正常或超前
        
        return "healthy"
    
    def _is_on_track(
        self,
        completed_tasks: int,
        total_tasks: int,
        days_remaining: Optional[int],
        goal: Goal
    ) -> bool:
        """
        判断目标是否按计划进行
        """
        if not days_remaining or days_remaining < 0:
            return False
        
        if total_tasks == 0:
            return True
        
        progress_percentage = (completed_tasks / total_tasks) * 100
        
        # 简单的线性判断：进度应该与时间消耗成正比
        if goal.deadline and hasattr(goal, 'created_at'):
            total_days = (goal.deadline - goal.created_at.date()).days
            expected_progress = ((total_days - days_remaining) / total_days * 100) if total_days > 0 else 0
            return progress_percentage >= expected_progress - 10  # 允许 10% 的偏差
        
        return progress_percentage >= 30  # 默认至少完成 30%
    
    def _get_upcoming_tasks(self, goal: Goal, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        获取即将到期的任务（未来 N 天内）
        """
        today = date.today()
        future_date = today + timedelta(days=days_ahead)
        
        upcoming = []
        for task in goal.tasks:
            if (task.due_date and 
                today <= task.due_date <= future_date and 
                task.status != "completed"):
                upcoming.append({
                    "task_id": str(task.id),
                    "title": task.title,
                    "due_date": task.due_date.isoformat(),
                    "priority": task.priority,
                    "days_until_due": (task.due_date - today).days,
                })
        
        return sorted(upcoming, key=lambda x: x["days_until_due"])
    
    async def _generate_ai_insights(
        self,
        goal: Goal,
        progress: Dict[str, Any],
        blockers: List[Dict[str, Any]],
        thread_id: str
    ) -> str:
        """
        使用 AI 生成进度分析和建议
        """
        prompt = f"""
作为一个项目进度分析专家，请分析以下目标的进度情况并提供建议：

**目标信息：**
- 标题：{goal.title}
- 类型：{goal.type}
- 截止日期：{goal.deadline}
- 状态：{goal.status}

**进度统计：**
- 总体进度：{progress['overall_progress']}%
- 里程碑完成：{progress['completed_milestones']}/{progress['total_milestones']}
- 任务完成：{progress['completed_tasks']}/{progress['total_tasks']}
- 剩余天数：{progress['days_remaining']} 天
- 时间健康度：{progress['time_health']}

**阻塞因素：**
{self._format_blockers_for_ai(blockers)}

请提供：
1. **进度评估**：当前进度是否正常？
2. **风险提示**：存在哪些主要风险？
3. **具体建议**：应该采取哪些行动来改善进度？
4. **下一步重点**：接下来应该优先完成什么？

请用简洁、可执行的语言给出建议。
"""
        
        try:
            ai_response = await self.chat_service.send_message(
                content=prompt,
                thread_id=thread_id,
                memory="Auto"
            )
            return ai_response
        except Exception as e:
            print(f"❌ AI 分析失败: {e}")
            return "AI 分析暂时不可用，请稍后再试。"
    
    async def _generate_weekly_ai_summary(
        self,
        summary: Dict[str, Any],
        thread_id: str
    ) -> str:
        """
        生成周度 AI 总结
        """
        prompt = f"""
请为用户生成本周的目标进度总结：

**总体情况：**
- 活跃目标数：{summary['total_active_goals']}
- 整体健康度：{summary['overall_health']}

**各目标进度：**
{self._format_goals_for_ai(summary['goals'])}

请提供：
1. **本周亮点**：哪些目标进展顺利？
2. **需要关注**：哪些目标需要特别注意？
3. **下周建议**：下周应该重点关注什么？

保持总结简洁、积极、可执行。
"""
        
        try:
            ai_response = await self.chat_service.send_message(
                content=prompt,
                thread_id=thread_id,
                memory="Auto"
            )
            return ai_response
        except Exception as e:
            print(f"❌ AI 总结失败: {e}")
            return "AI 总结暂时不可用。"
    
    def _format_blockers_for_ai(self, blockers: List[Dict[str, Any]]) -> str:
        """格式化阻塞因素用于 AI 提示"""
        if not blockers:
            return "无明显阻塞"
        
        formatted = []
        for blocker in blockers[:5]:  # 只显示前 5 个
            formatted.append(
                f"- [{blocker['severity']}] {blocker['message']}"
            )
        return "\n".join(formatted)
    
    def _format_goals_for_ai(self, goals: List[Dict[str, Any]]) -> str:
        """格式化目标列表用于 AI 提示"""
        formatted = []
        for goal in goals:
            formatted.append(
                f"- {goal['title']}: {goal['progress']}% ({goal['time_health']}, {goal['blocker_count']} 个阻塞)"
            )
        return "\n".join(formatted)
