"""
测试 ProgressService 的功能
"""
from datetime import date, timedelta
from unittest.mock import AsyncMock, patch
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.core.db import Base
from backend.models.goal import Goal
from backend.models.milestone import Milestone
from backend.models.task import Task
from backend.services.progress_service import ProgressService


# 使用内存数据库进行测试
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_session():
    """创建测试数据库会话"""
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def progress_service(db_session):
    """创建 ProgressService 实例"""
    return ProgressService(db_session)


@pytest.fixture
def sample_goal_with_tasks(db_session):
    """创建带有里程碑和任务的示例目标"""
    goal = Goal(
        memory_id="test-memory-progress",
        title="学习 Python",
        type="study",
        deadline=date.today() + timedelta(days=30)
    )
    db_session.add(goal)
    db_session.commit()
    db_session.refresh(goal)
    
    # 添加里程碑
    milestone1 = Milestone(
        goal_id=goal.id,
        title="基础知识",
        target_date=date.today() + timedelta(days=15),
        definition_of_done="完成基础学习",
        order=1,
        status="completed"  # 已完成
    )
    milestone2 = Milestone(
        goal_id=goal.id,
        title="进阶知识",
        target_date=date.today() + timedelta(days=30),
        definition_of_done="完成进阶学习",
        order=2,
        status="in_progress"
    )
    db_session.add_all([milestone1, milestone2])
    db_session.commit()
    db_session.refresh(milestone1)
    db_session.refresh(milestone2)
    
    # 添加任务
    task1 = Task(
        goal_id=goal.id,
        milestone_id=milestone1.id,
        title="任务 1",
        due_date=date.today() + timedelta(days=5),
        status="completed",
        priority="high",
        estimated_time=5
    )
    task2 = Task(
        goal_id=goal.id,
        milestone_id=milestone1.id,
        title="任务 2",
        due_date=date.today() + timedelta(days=10),
        status="completed",
        priority="medium",
        estimated_time=3
    )
    task3 = Task(
        goal_id=goal.id,
        milestone_id=milestone2.id,
        title="任务 3",
        due_date=date.today() + timedelta(days=20),
        status="in_progress",
        priority="high",
        estimated_time=8
    )
    task4 = Task(
        goal_id=goal.id,
        milestone_id=milestone2.id,
        title="任务 4",
        due_date=date.today() + timedelta(days=25),
        status="pending",
        priority="medium",
        estimated_time=4
    )
    db_session.add_all([task1, task2, task3, task4])
    db_session.commit()
    
    return goal


class TestProgressService:
    """测试 ProgressService 类"""

    def test_calculate_progress(self, progress_service, sample_goal_with_tasks):
        """测试基础进度计算"""
        progress = progress_service.calculate_progress(sample_goal_with_tasks.id)
        
        assert progress is not None
        assert progress["goal_id"] == str(sample_goal_with_tasks.id)
        assert progress["goal_title"] == "学习 Python"
        assert progress["total_tasks"] == 4
        assert progress["completed_tasks"] == 2
        assert progress["task_progress"] == 50.0
        assert progress["total_milestones"] == 2
        assert progress["completed_milestones"] == 1
        assert progress["milestone_progress"] == 50.0
        assert progress["overall_progress"] == 50.0
        assert progress["days_remaining"] == 30
        assert "time_health" in progress
        assert "on_track" in progress

    def test_get_milestone_progress(self, progress_service, sample_goal_with_tasks, db_session):
        """测试获取里程碑进度"""
        milestone = db_session.query(Milestone).filter(
            Milestone.goal_id == sample_goal_with_tasks.id,
            Milestone.order == 1
        ).first()
        
        progress = progress_service.get_milestone_progress(milestone.id)
        
        assert progress is not None
        assert progress["milestone_id"] == str(milestone.id)
        assert progress["milestone_title"] == "基础知识"
        assert progress["status"] == "completed"
        assert progress["total_tasks"] == 2
        assert progress["completed_tasks"] == 2
        assert progress["progress_percentage"] == 100.0

    def test_identify_blockers_overdue_task(self, progress_service, db_session):
        """测试识别逾期任务"""
        # 创建一个有逾期任务的目标
        goal = Goal(
            memory_id="test-overdue",
            title="测试逾期",
            type="study",
            deadline=date.today() + timedelta(days=10)
        )
        db_session.add(goal)
        db_session.commit()
        db_session.refresh(goal)
        
        milestone = Milestone(
            goal_id=goal.id,
            title="测试里程碑",
            target_date=date.today() + timedelta(days=10),
            definition_of_done="完成",
            order=1
        )
        db_session.add(milestone)
        db_session.commit()
        db_session.refresh(milestone)
        
        # 逾期任务
        overdue_task = Task(
            goal_id=goal.id,
            milestone_id=milestone.id,
            title="逾期任务",
            due_date=date.today() - timedelta(days=5),  # 5 天前就该完成
            status="in_progress",
            priority="high",
            estimated_time=5
        )
        db_session.add(overdue_task)
        db_session.commit()
        
        blockers = progress_service.identify_blockers(goal.id)
        
        assert len(blockers) >= 1
        overdue_blocker = next((b for b in blockers if b["type"] == "overdue_task"), None)
        assert overdue_blocker is not None
        assert overdue_blocker["severity"] == "high"
        assert overdue_blocker["days_overdue"] == 5

    def test_identify_blockers_overdue_milestone(self, progress_service, db_session):
        """测试识别逾期里程碑"""
        goal = Goal(
            memory_id="test-overdue-milestone",
            title="测试逾期里程碑",
            type="study",
            deadline=date.today() + timedelta(days=10)
        )
        db_session.add(goal)
        db_session.commit()
        db_session.refresh(goal)
        
        # 逾期里程碑
        overdue_milestone = Milestone(
            goal_id=goal.id,
            title="逾期里程碑",
            target_date=date.today() - timedelta(days=3),
            definition_of_done="应该完成了",
            order=1,
            status="in_progress"
        )
        db_session.add(overdue_milestone)
        db_session.commit()
        
        blockers = progress_service.identify_blockers(goal.id)
        
        assert len(blockers) >= 1
        milestone_blocker = next((b for b in blockers if b["type"] == "overdue_milestone"), None)
        assert milestone_blocker is not None
        assert milestone_blocker["severity"] == "critical"

    def test_identify_blockers_urgent_task(self, progress_service, db_session):
        """测试识别即将到期的高优先级任务"""
        goal = Goal(
            memory_id="test-urgent",
            title="测试紧急任务",
            type="study",
            deadline=date.today() + timedelta(days=10)
        )
        db_session.add(goal)
        db_session.commit()
        db_session.refresh(goal)
        
        milestone = Milestone(
            goal_id=goal.id,
            title="测试里程碑",
            target_date=date.today() + timedelta(days=10),
            definition_of_done="完成",
            order=1
        )
        db_session.add(milestone)
        db_session.commit()
        db_session.refresh(milestone)
        
        # 即将到期的高优先级任务
        urgent_task = Task(
            goal_id=goal.id,
            milestone_id=milestone.id,
            title="紧急任务",
            due_date=date.today() + timedelta(days=2),  # 2 天后到期
            status="pending",
            priority="high",
            estimated_time=5
        )
        db_session.add(urgent_task)
        db_session.commit()
        
        blockers = progress_service.identify_blockers(goal.id)
        
        urgent_blocker = next((b for b in blockers if b["type"] == "urgent_task"), None)
        assert urgent_blocker is not None
        assert urgent_blocker["severity"] == "medium"
        assert urgent_blocker["days_until_due"] == 2

    @pytest.mark.asyncio
    async def test_generate_progress_report(self, progress_service, sample_goal_with_tasks):
        """测试生成进度报告"""
        # Mock AI 服务
        with patch.object(
            progress_service.chat_service,
            'send_message',
            new_callable=AsyncMock
        ) as mock_send_message:
            mock_send_message.return_value = "这是 AI 生成的进度分析和建议"
            
            report = await progress_service.generate_progress_report(
                goal_id=sample_goal_with_tasks.id,
                thread_id="test-thread-123",
                include_ai_insights=True
            )
            
            assert report is not None
            assert "goal" in report
            assert "progress" in report
            assert "milestones" in report
            assert "blockers" in report
            assert "upcoming_tasks" in report
            assert "ai_insights" in report
            assert report["goal"]["title"] == "学习 Python"
            assert len(report["milestones"]) == 2
            
            # 验证 AI 被调用
            mock_send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_progress_report_without_ai(self, progress_service, sample_goal_with_tasks):
        """测试生成不含 AI 的进度报告"""
        report = await progress_service.generate_progress_report(
            goal_id=sample_goal_with_tasks.id,
            thread_id="test-thread-123",
            include_ai_insights=False
        )
        
        assert report is not None
        assert "ai_insights" not in report
        assert "progress" in report
        assert "blockers" in report

    def test_get_at_risk_goals(self, progress_service, db_session):
        """测试获取有风险的目标"""
        # 创建一个进度落后的目标
        at_risk_goal = Goal(
            memory_id="test-at-risk",
            title="落后的目标",
            type="study",
            deadline=date.today() + timedelta(days=5),  # 快要截止了
            status="in_progress"
        )
        db_session.add(at_risk_goal)
        db_session.commit()
        db_session.refresh(at_risk_goal)
        
        milestone = Milestone(
            goal_id=at_risk_goal.id,
            title="测试里程碑",
            target_date=date.today() + timedelta(days=5),
            definition_of_done="完成",
            order=1,
            status="not_started"
        )
        db_session.add(milestone)
        db_session.commit()
        db_session.refresh(milestone)
        
        task = Task(
            goal_id=at_risk_goal.id,
            milestone_id=milestone.id,
            title="任务",
            due_date=date.today() + timedelta(days=5),
            status="pending",
            priority="high",
            estimated_time=10
        )
        db_session.add(task)
        db_session.commit()
        
        at_risk = progress_service.get_at_risk_goals()
        
        assert len(at_risk) >= 1
        risk_goal = next((g for g in at_risk if g["goal_title"] == "落后的目标"), None)
        assert risk_goal is not None
        assert len(risk_goal["risk_factors"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
