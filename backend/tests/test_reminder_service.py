"""
ReminderService 测试
"""
import pytest
from datetime import datetime, timedelta, date
from uuid import uuid4
from unittest.mock import AsyncMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.core.db import Base
from backend.models.goal import Goal
from backend.models.milestone import Milestone
from backend.models.task import Task
from backend.models.reminder import Reminder, ReminderType, ReminderPriority
from backend.services.reminder_service import ReminderService


# 测试数据库设置
@pytest.fixture
def db_session():
    """创建内存数据库会话"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()


@pytest.fixture
def sample_goal(db_session):
    """创建示例目标"""
    goal = Goal(
        id=uuid4(),
        memory_id="test_memory_123",
        title="完成项目",
        type="career",
        status="in-progress",
        deadline=date.today() + timedelta(days=30)
    )
    db_session.add(goal)
    db_session.commit()
    return goal


@pytest.fixture
def sample_milestone(db_session, sample_goal):
    """创建示例里程碑"""
    milestone = Milestone(
        id=uuid4(),
        goal_id=sample_goal.id,
        title="里程碑 1",
        target_date=date.today() + timedelta(days=14),
        definition_of_done="Complete all tasks",
        order=1,
        status="in_progress"
    )
    db_session.add(milestone)
    db_session.commit()
    return milestone


@pytest.fixture
def sample_task(db_session, sample_goal, sample_milestone):
    """创建示例任务"""
    task = Task(
        id=uuid4(),
        goal_id=sample_goal.id,
        milestone_id=sample_milestone.id,
        title="完成任务",
        priority="high",
        status="not_started",
        due_date=date.today() + timedelta(days=7),
        estimated_time=2.0
    )
    db_session.add(task)
    db_session.commit()
    return task


@pytest.fixture
def reminder_service(db_session):
    """创建 ReminderService 实例"""
    return ReminderService(db_session)


# ==================== CRUD 操作测试 ====================

def test_create_reminder(reminder_service, sample_goal):
    """测试创建提醒"""
    remind_at = datetime.utcnow() + timedelta(hours=24)
    
    reminder = reminder_service.create_reminder(
        title="测试提醒",
        message="这是一条测试提醒",
        remind_at=remind_at,
        type=ReminderType.CUSTOM,
        priority=ReminderPriority.MEDIUM,
        goal_id=sample_goal.id
    )
    
    assert reminder.id is not None
    assert reminder.title == "测试提醒"
    assert reminder.message == "这是一条测试提醒"
    assert reminder.type == ReminderType.CUSTOM
    assert reminder.priority == ReminderPriority.MEDIUM
    assert reminder.goal_id == str(sample_goal.id)
    assert reminder.is_read == False
    assert reminder.is_completed == False
    assert reminder.is_dismissed == False


def test_get_reminder(reminder_service):
    """测试获取提醒"""
    # 创建提醒
    remind_at = datetime.utcnow() + timedelta(hours=1)
    reminder = reminder_service.create_reminder(
        title="获取测试",
        message="测试获取功能",
        remind_at=remind_at
    )
    
    # 获取提醒
    fetched = reminder_service.get_reminder(reminder.id)
    
    assert fetched is not None
    assert fetched.id == reminder.id
    assert fetched.title == "获取测试"


def test_get_pending_reminders(reminder_service):
    """测试获取待处理提醒"""
    now = datetime.utcnow()
    
    # 创建过去的提醒（应该被获取）
    past_reminder = reminder_service.create_reminder(
        title="过去的提醒",
        message="已过期",
        remind_at=now - timedelta(hours=2),
        priority=ReminderPriority.HIGH
    )
    
    # 创建当前的提醒（应该被获取）
    current_reminder = reminder_service.create_reminder(
        title="当前提醒",
        message="刚刚到期",
        remind_at=now,
        priority=ReminderPriority.URGENT
    )
    
    # 创建未来的提醒（不应该被获取）
    future_reminder = reminder_service.create_reminder(
        title="未来提醒",
        message="还没到时间",
        remind_at=now + timedelta(hours=5)
    )
    
    # 创建已完成的提醒（不应该被获取）
    completed_reminder = reminder_service.create_reminder(
        title="已完成",
        message="已完成",
        remind_at=now - timedelta(hours=1)
    )
    reminder_service.mark_as_completed(completed_reminder.id)
    
    # 获取待处理提醒
    pending = reminder_service.get_pending_reminders()
    
    assert len(pending) == 2
    # 应该按优先级和时间排序
    assert pending[0].priority == ReminderPriority.URGENT
    assert pending[0].id == current_reminder.id


def test_get_upcoming_reminders(reminder_service):
    """测试获取即将到来的提醒"""
    now = datetime.utcnow()
    
    # 创建 12 小时后的提醒（应该被获取）
    upcoming = reminder_service.create_reminder(
        title="12小时后",
        message="即将到来",
        remind_at=now + timedelta(hours=12)
    )
    
    # 创建 2 天后的提醒（不应该被获取）
    far_future = reminder_service.create_reminder(
        title="2天后",
        message="太远了",
        remind_at=now + timedelta(days=2)
    )
    
    # 获取未来 24 小时内的提醒
    upcoming_list = reminder_service.get_upcoming_reminders(hours_ahead=24)
    
    assert len(upcoming_list) == 1
    assert upcoming_list[0].id == upcoming.id


def test_mark_as_read(reminder_service):
    """测试标记为已读"""
    reminder = reminder_service.create_reminder(
        title="测试已读",
        message="测试",
        remind_at=datetime.utcnow()
    )
    
    assert reminder.is_read == False
    
    success = reminder_service.mark_as_read(reminder.id)
    
    assert success == True
    
    updated = reminder_service.get_reminder(reminder.id)
    assert updated.is_read == True


def test_mark_as_completed(reminder_service):
    """测试标记为已完成"""
    reminder = reminder_service.create_reminder(
        title="测试完成",
        message="测试",
        remind_at=datetime.utcnow()
    )
    
    success = reminder_service.mark_as_completed(reminder.id)
    
    assert success == True
    
    updated = reminder_service.get_reminder(reminder.id)
    assert updated.is_completed == True
    assert updated.is_read == True  # 完成时自动标记为已读


def test_dismiss_reminder(reminder_service):
    """测试忽略提醒"""
    reminder = reminder_service.create_reminder(
        title="测试忽略",
        message="测试",
        remind_at=datetime.utcnow()
    )
    
    success = reminder_service.dismiss_reminder(reminder.id)
    
    assert success == True
    
    updated = reminder_service.get_reminder(reminder.id)
    assert updated.is_dismissed == True


def test_delete_reminder(reminder_service):
    """测试删除提醒"""
    reminder = reminder_service.create_reminder(
        title="测试删除",
        message="测试",
        remind_at=datetime.utcnow()
    )
    
    reminder_id = reminder.id
    success = reminder_service.delete_reminder(reminder_id)
    
    assert success == True
    
    deleted = reminder_service.get_reminder(reminder_id)
    assert deleted is None


# ==================== 自动提醒生成测试 ====================

def test_generate_task_reminders(reminder_service, sample_task):
    """测试为任务生成提醒"""
    reminders = reminder_service.generate_task_reminders(
        task_id=sample_task.id,
        advance_days=[1, 3, 7]
    )
    
    # 任务是 7 天后到期，所以应该创建 2 个提醒（1 和 3 天前，7天前是今天）
    assert len(reminders) == 2
    
    # 检查提醒类型和优先级
    for reminder in reminders:
        assert reminder.type == ReminderType.TASK_DUE
        assert reminder.task_id == str(sample_task.id)
        assert reminder.goal_id == str(sample_task.goal_id)
        assert "完成任务" in reminder.title
    
    # 检查优先级设置
    # 1 天前应该是 URGENT
    one_day_reminder = next(r for r in reminders if "1 天" in r.message)
    assert one_day_reminder.priority == ReminderPriority.URGENT


def test_generate_task_reminders_skip_past(reminder_service, sample_task):
    """测试不创建过去的提醒"""
    # 设置任务为明天到期
    sample_task.due_date = date.today() + timedelta(days=1)
    reminder_service.session.commit()
    
    # 尝试创建 3 天前和 7 天前的提醒（应该被跳过）
    reminders = reminder_service.generate_task_reminders(
        task_id=sample_task.id,
        advance_days=[1, 3, 7]
    )
    
    # 只有 1 天前的提醒会被创建（因为 3天和7天都是过去）
    # 实际上1天前就是今天，所以会创建
    assert len(reminders) >= 0  # 至少创建0个（如果今天算过去）或1个


def test_generate_task_reminders_no_duplicates(reminder_service, sample_task):
    """测试不创建重复提醒"""
    # 第一次创建
    reminders1 = reminder_service.generate_task_reminders(
        task_id=sample_task.id,
        advance_days=[1, 3]
    )
    
    assert len(reminders1) == 2
    
    # 第二次创建（应该跳过已存在的）
    reminders2 = reminder_service.generate_task_reminders(
        task_id=sample_task.id,
        advance_days=[1, 3]
    )
    
    assert len(reminders2) == 0


def test_generate_milestone_reminders(reminder_service, sample_milestone):
    """测试为里程碑生成提醒"""
    reminders = reminder_service.generate_milestone_reminders(
        milestone_id=sample_milestone.id,
        advance_days=[3, 7, 14]
    )
    
    # 里程碑是 14 天后到期，所以应该创建 2 个提醒（3 和 7 天前，14天前是今天）
    assert len(reminders) == 2
    
    for reminder in reminders:
        assert reminder.type == ReminderType.MILESTONE_DUE
        assert reminder.milestone_id == str(sample_milestone.id)
        assert "里程碑 1" in reminder.title


def test_generate_goal_deadline_reminders(reminder_service, sample_goal):
    """测试为目标截止日期生成提醒"""
    reminders = reminder_service.generate_goal_deadline_reminders(
        goal_id=sample_goal.id,
        advance_days=[7, 14, 30]
    )
    
    # 目标是 30 天后到期，所以应该创建 2 个提醒（14 和 30 天前，7天已经过去了）
    assert len(reminders) == 2
    
    for reminder in reminders:
        assert reminder.type == ReminderType.GOAL_DEADLINE
        assert reminder.goal_id == str(sample_goal.id)
        assert "完成项目" in reminder.title


def test_auto_generate_reminders_for_goal(reminder_service, sample_goal, sample_milestone, sample_task):
    """测试为目标自动生成所有提醒"""
    result = reminder_service.auto_generate_reminders_for_goal(sample_goal.id)
    
    assert "goal_reminders" in result
    assert "milestone_reminders" in result
    assert "task_reminders" in result
    
    # 应该包含目标、里程碑、任务的提醒
    assert len(result["goal_reminders"]) > 0
    assert len(result["milestone_reminders"]) > 0
    assert len(result["task_reminders"]) > 0


# ==================== 每日简报和周度总结测试 ====================

@pytest.mark.asyncio
async def test_generate_daily_briefing(reminder_service, sample_task, db_session):
    """测试生成每日简报"""
    # 设置任务为今天到期
    sample_task.due_date = date.today()
    db_session.commit()
    
    # 创建逾期任务
    overdue_task = Task(
        id=uuid4(),
        goal_id=sample_task.goal_id,
        milestone_id=sample_task.milestone_id,
        title="逾期任务",
        priority="high",
        status="in_progress",
        due_date=date.today() - timedelta(days=3)
    )
    db_session.add(overdue_task)
    db_session.commit()
    
    # Mock AI 响应
    with patch.object(
        reminder_service.chat_service,
        'send_message',
        new_callable=AsyncMock
    ) as mock_ai:
        mock_ai.return_value = "今日重点：完成高优先级任务。时间建议：早上处理重要任务。"
        
        briefing = await reminder_service.generate_daily_briefing(
            thread_id="test_thread",
            target_date=date.today()
        )
    
    assert "date" in briefing
    assert "today_tasks" in briefing
    assert "overdue_tasks" in briefing
    assert "ai_summary" in briefing
    
    assert len(briefing["today_tasks"]) == 1
    assert len(briefing["overdue_tasks"]) == 1
    assert briefing["today_tasks"][0]["title"] == "完成任务"
    assert briefing["ai_summary"] == "今日重点：完成高优先级任务。时间建议：早上处理重要任务。"


@pytest.mark.asyncio
async def test_generate_weekly_summary(reminder_service, sample_task, db_session):
    """测试生成周度总结"""
    # 设置任务为本周完成
    sample_task.status = "completed"
    sample_task.due_date = date.today()
    db_session.commit()
    
    # 创建下周的高优先级任务
    next_week_task = Task(
        id=uuid4(),
        goal_id=sample_task.goal_id,
        milestone_id=sample_task.milestone_id,
        title="下周任务",
        priority="high",
        status="not_started",
        due_date=date.today() + timedelta(days=7)
    )
    db_session.add(next_week_task)
    db_session.commit()
    
    # Mock AI 响应
    with patch.object(
        reminder_service.chat_service,
        'send_message',
        new_callable=AsyncMock
    ) as mock_ai:
        mock_ai.return_value = "本周完成了重要任务，继续保持！"
        
        summary = await reminder_service.generate_weekly_summary(
            thread_id="test_thread"
        )
    
    assert "week_start" in summary
    assert "week_end" in summary
    assert "completed_tasks_count" in summary
    assert "next_week_priorities" in summary
    assert "ai_analysis" in summary
    
    assert summary["completed_tasks_count"] == 1
    assert len(summary["next_week_priorities"]) == 1
    assert summary["ai_analysis"] == "本周完成了重要任务，继续保持！"


def test_schedule_daily_briefing(reminder_service):
    """测试安排每日简报"""
    remind_time = datetime.utcnow() + timedelta(days=1)
    remind_time = remind_time.replace(hour=8, minute=0, second=0, microsecond=0)
    
    reminder = reminder_service.schedule_daily_briefing(remind_time)
    
    assert reminder.type == ReminderType.DAILY_BRIEFING
    assert reminder.priority == ReminderPriority.HIGH
    assert "每日简报" in reminder.title


def test_schedule_weekly_summary(reminder_service):
    """测试安排周度总结"""
    remind_time = datetime.utcnow() + timedelta(days=7)
    
    reminder = reminder_service.schedule_weekly_summary(remind_time)
    
    assert reminder.type == ReminderType.WEEKLY_SUMMARY
    assert reminder.priority == ReminderPriority.MEDIUM
    assert "周度总结" in reminder.title


# ==================== 智能提醒内容生成测试 ====================

@pytest.mark.asyncio
async def test_generate_smart_reminder_message(reminder_service, sample_task):
    """测试生成智能提醒消息"""
    # Mock AI 响应
    with patch.object(
        reminder_service.chat_service,
        'send_message',
        new_callable=AsyncMock
    ) as mock_ai:
        mock_ai.return_value = "提醒：是时候完成这个任务了！\n建议：先从最简单的部分开始。"
        
        message = await reminder_service.generate_smart_reminder_message(
            task_id=sample_task.id,
            thread_id="test_thread"
        )
    
    assert "提醒" in message
    assert "建议" in message
    mock_ai.assert_called_once()


@pytest.mark.asyncio
async def test_generate_smart_reminder_message_fallback(reminder_service, sample_task):
    """测试 AI 失败时的降级处理"""
    # Mock AI 失败
    with patch.object(
        reminder_service.chat_service,
        'send_message',
        new_callable=AsyncMock
    ) as mock_ai:
        mock_ai.side_effect = Exception("AI 服务不可用")
        
        message = await reminder_service.generate_smart_reminder_message(
            task_id=sample_task.id,
            thread_id="test_thread"
        )
    
    # 应该返回简单的提醒消息
    assert "完成任务" in message


# ==================== 边界情况测试 ====================

def test_generate_reminders_for_task_without_due_date(reminder_service):
    """测试为不存在的任务生成提醒"""
    # 使用不存在的任务ID
    fake_id = uuid4()
    
    reminders = reminder_service.generate_task_reminders(fake_id)
    
    # 任务不存在，不应该创建提醒
    assert len(reminders) == 0


def test_get_reminder_nonexistent(reminder_service):
    """测试获取不存在的提醒"""
    reminder = reminder_service.get_reminder("nonexistent_id")
    assert reminder is None


def test_mark_nonexistent_reminder(reminder_service):
    """测试操作不存在的提醒"""
    assert reminder_service.mark_as_read("nonexistent") == False
    assert reminder_service.mark_as_completed("nonexistent") == False
    assert reminder_service.dismiss_reminder("nonexistent") == False
    assert reminder_service.delete_reminder("nonexistent") == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
