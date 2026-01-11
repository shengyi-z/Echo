"""
Reminder Model - 提醒通知数据模型
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from uuid import uuid4
import enum

from ..core.db import Base


class ReminderType(str, enum.Enum):
    """提醒类型"""
    TASK_DUE = "task_due"              # 任务到期
    MILESTONE_DUE = "milestone_due"    # 里程碑到期
    GOAL_DEADLINE = "goal_deadline"    # 目标截止
    DAILY_BRIEFING = "daily_briefing"  # 每日简报
    WEEKLY_SUMMARY = "weekly_summary"  # 周度总结
    CUSTOM = "custom"                   # 自定义提醒


class ReminderPriority(str, enum.Enum):
    """提醒优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Reminder(Base):
    """
    提醒通知表
    存储所有类型的提醒，包括任务提醒、里程碑提醒、每日简报等
    """
    __tablename__ = "reminders"
    
    id = Column(String(36), primary_key=True, default=lambda: uuid4().hex)
    
    # 关联关系
    goal_id = Column(String(36), ForeignKey("goals.id", ondelete="CASCADE"), nullable=True)
    milestone_id = Column(String(36), ForeignKey("milestones.id", ondelete="CASCADE"), nullable=True)
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True)
    
    # 提醒内容
    type = Column(SQLEnum(ReminderType), nullable=False)
    priority = Column(SQLEnum(ReminderPriority), default=ReminderPriority.MEDIUM)
    title = Column(String(200), nullable=False)
    message = Column(String(1000), nullable=False)
    
    # 时间管理
    remind_at = Column(DateTime, nullable=False)  # 提醒时间
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 状态管理
    is_read = Column(Boolean, default=False)      # 是否已读
    is_completed = Column(Boolean, default=False)  # 是否已完成
    is_dismissed = Column(Boolean, default=False)  # 是否已忽略
    
    # 关联实体
    goal = relationship("Goal", back_populates="reminders")
    milestone = relationship("Milestone", back_populates="reminders")
    task = relationship("Task", back_populates="reminders")
    
    def __repr__(self):
        return f"<Reminder(id={self.id}, type={self.type}, title={self.title})>"
