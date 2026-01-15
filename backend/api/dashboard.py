"""
Dashboard API - Provide aggregated goal and task data for dashboard view
"""
from datetime import date, timedelta
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.db import SessionLocal
from ..repo.goal_repo import GoalRepository
from ..models.goal import Goal

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


class NextMilestone(BaseModel):
    title: str
    target_date: date


class ActiveGoalData(BaseModel):
    title: str
    type: str
    deadline: date
    progress_percentage: int
    next_milestone: Optional[NextMilestone]
    nearest_deadline: Optional[date]


class TodayTask(BaseModel):
    id: str
    title: str
    priority: str
    estimated_time: float


class RiskAlert(BaseModel):
    message: str
    severity: str


class DashboardData(BaseModel):
    active_goal: Optional[ActiveGoalData]
    today_tasks: List[TodayTask]
    risk_alerts: List[RiskAlert]


@router.get("/data", response_model=DashboardData)
async def get_dashboard_data(memory_id: Optional[str] = None):
    """
    获取Dashboard所需的所有数据：
    - 当前活跃的goal
    - 今天的Top 3任务
    - Risk alerts
    """
    session = SessionLocal()
    try:
        goal_repo = GoalRepository(session)
        
        # 获取所有goals，取第一个作为active goal
        goals = session.query(Goal).all()
        
        if not goals:
            # 没有goal，返回空数据
            return DashboardData(
                active_goal=None,
                today_tasks=[],
                risk_alerts=[]
            )
        
        goal = goals[0]
        
        # 加载goal的完整数据（包括milestones和tasks）
        full_goal = goal_repo.get_goal(goal.id, include_children=True)
        
        # 计算进度百分比
        total_tasks = len(full_goal.tasks)
        completed_tasks = sum(1 for task in full_goal.tasks if task.status == "completed")
        progress = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0
        
        # 获取下一个milestone
        next_milestone = None
        today = date.today()
        upcoming_milestones = [
            m for m in full_goal.milestones 
            if m.target_date >= today and m.status != "completed"
        ]
        if upcoming_milestones:
            upcoming_milestones.sort(key=lambda m: m.target_date)
            next_ms = upcoming_milestones[0]
            next_milestone = NextMilestone(
                title=next_ms.title,
                target_date=next_ms.target_date
            )
        
        # 获取最近的deadline
        nearest_deadline = None
        upcoming_tasks = [
            t for t in full_goal.tasks 
            if t.due_date >= today and t.status != "completed"
        ]
        if upcoming_tasks:
            upcoming_tasks.sort(key=lambda t: t.due_date)
            nearest_deadline = upcoming_tasks[0].due_date
        
        active_goal = ActiveGoalData(
            title=full_goal.title,
            type=full_goal.type,
            deadline=full_goal.deadline,
            progress_percentage=progress,
            next_milestone=next_milestone,
            nearest_deadline=nearest_deadline
        )
        
        # 获取今天的Top 3任务（高优先级 + 最近due date）
        today_end = today + timedelta(days=1)
        priority_order = {"high": 0, "medium": 1, "low": 2}
        
        incomplete_tasks = [
            t for t in full_goal.tasks
            if t.status != "completed" and t.due_date >= today
        ]
        
        # 按优先级和due_date排序
        incomplete_tasks.sort(
            key=lambda t: (priority_order.get(t.priority, 3), t.due_date)
        )
        
        today_tasks = [
            TodayTask(
                id=str(task.id),
                title=task.title,
                priority=task.priority,
                estimated_time=task.estimated_time
            )
            for task in incomplete_tasks[:3]
        ]
        
        # 生成risk alerts（基于任务和里程碑的状态）
        risk_alerts = []
        
        # 检查即将到期的任务
        for task in incomplete_tasks[:5]:
            days_until_due = (task.due_date - today).days
            if days_until_due <= 2 and task.priority == "high":
                risk_alerts.append(RiskAlert(
                    message=f"High priority task '{task.title}' is due in {days_until_due} days",
                    severity="high"
                ))
        
        # 检查里程碑进度
        for milestone in full_goal.milestones:
            if milestone.status != "completed" and milestone.target_date >= today:
                milestone_tasks = [t for t in full_goal.tasks if t.milestone_id == milestone.id]
                completed = sum(1 for t in milestone_tasks if t.status == "completed")
                total = len(milestone_tasks)
                
                if total > 0:
                    completion_rate = completed / total
                    days_until_milestone = (milestone.target_date - today).days
                    
                    # 如果距离里程碑很近但完成率很低
                    if days_until_milestone <= 7 and completion_rate < 0.5:
                        risk_alerts.append(RiskAlert(
                            message=f"Milestone '{milestone.title}' is {int(completion_rate * 100)}% complete but due in {days_until_milestone} days",
                            severity="medium"
                        ))
        
        return DashboardData(
            active_goal=active_goal,
            today_tasks=today_tasks,
            risk_alerts=risk_alerts[:3]  # 最多显示3个alerts
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard data: {str(e)}")
    finally:
        session.close()
