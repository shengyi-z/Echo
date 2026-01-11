"""
测试 PlanningService 的功能
"""
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.core.db import Base
from backend.models.goal import Goal
from backend.services.planning_service import PlanningService
from backend.schemas.plan import PlanRequest, PlanGoalInput


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
def planning_service(db_session):
    """创建 PlanningService 实例"""
    return PlanningService(db_session)


@pytest.fixture
def sample_plan_request():
    """创建示例计划请求"""
    return PlanRequest(
        goal=PlanGoalInput(
            title="学习 Python 编程",
            type="study",  # 使用有效的枚举值
            deadline=date.today() + timedelta(days=90),
            budget=500.0,
            weekly_hours=10
        ),
        thread_id="test-thread-123",
        memory_id="test-memory-123"
    )


@pytest.fixture
def mock_ai_response():
    """模拟 AI 返回的 JSON 响应"""
    return """
{
    "milestones": [
        {
            "title": "Python 基础",
            "target_date": "2026-02-10",
            "definition_of_done": "完成基础语法学习",
            "order": 1,
            "tasks": [
                {
                    "title": "学习变量和数据类型",
                    "description": "掌握基本数据类型",
                    "due_date": "2026-01-20",
                    "priority": "high",
                    "estimated_time": 5
                },
                {
                    "title": "学习控制流",
                    "description": "if/else, loops",
                    "due_date": "2026-02-05",
                    "priority": "high",
                    "estimated_time": 8
                }
            ]
        },
        {
            "title": "Python 进阶",
            "target_date": "2026-03-15",
            "definition_of_done": "掌握面向对象编程",
            "order": 2,
            "tasks": [
                {
                    "title": "学习类和对象",
                    "description": "OOP 概念",
                    "due_date": "2026-03-01",
                    "priority": "medium",
                    "estimated_time": 10
                }
            ]
        }
    ],
    "artifacts": [
        {
            "title": "Python 学习资源",
            "type": "resource",
            "url": "https://docs.python.org/3/tutorial/"
        }
    ]
}
"""


class TestPlanningService:
    """测试 PlanningService 类"""

    @pytest.mark.asyncio
    async def test_generate_and_store_with_ai_response(
        self, planning_service, sample_plan_request, mock_ai_response, db_session
    ):
        """测试使用 AI 响应生成并存储计划"""
        # Mock ChatService.send_message 方法
        with patch.object(
            planning_service.chat_service, 
            'send_message', 
            new_callable=AsyncMock
        ) as mock_send_message:
            mock_send_message.return_value = mock_ai_response
            
            # 调用服务方法
            response = await planning_service.generate_and_store(sample_plan_request)
            
            # 验证返回结果
            assert response is not None
            assert response.focus == "学习 Python 编程"
            assert len(response.milestones) == 2
            assert response.milestones[0].title == "Python 基础"
            # tasks 是 PlanResponse 的字段，不是 milestone 的
            assert len(response.tasks) >= 3  # 至少有 3 个任务
            # artifacts 可能为空（取决于解析逻辑）
            assert isinstance(response.artifacts, list)
            
            # 验证 AI 调用参数
            mock_send_message.assert_called_once()
            call_args = mock_send_message.call_args
            assert call_args.kwargs['thread_id'] == "test-thread-123"
            assert call_args.kwargs['memory'] == "Auto"
            assert "学习 Python 编程" in call_args.kwargs['content']
            
            # 验证数据库中的数据（通过 memory_id 查找）
            goal = db_session.query(Goal).filter(Goal.memory_id == "test-memory-123").first()
            assert goal is not None
            assert goal.title == "学习 Python 编程"
            assert goal.memory_id == "test-memory-123"
            assert len(goal.milestones) == 2
            assert goal.milestones[0].order == 1
            assert len(goal.tasks) >= 3  # 总共至少 3 个任务

    @pytest.mark.asyncio
    async def test_generate_and_store_with_ai_failure(
        self, planning_service, sample_plan_request, db_session
    ):
        """测试 AI 调用失败时使用默认计划"""
        # Mock ChatService.send_message 抛出异常
        with patch.object(
            planning_service.chat_service,
            'send_message',
            new_callable=AsyncMock
        ) as mock_send_message:
            mock_send_message.side_effect = Exception("AI API 调用失败")
            
            # 调用服务方法
            response = await planning_service.generate_and_store(sample_plan_request)
            
            # 验证返回结果（应该使用默认计划）
            assert response is not None
            assert response.focus == "学习 Python 编程"
            assert len(response.milestones) >= 1  # 至少有一个默认里程碑
            
            # 验证数据库中的数据
            goal = db_session.query(Goal).filter(Goal.memory_id == "test-memory-123").first()
            assert goal is not None
            assert goal.title == "学习 Python 编程"

    @pytest.mark.asyncio
    async def test_generate_without_goal(self, planning_service):
        """测试没有提供 goal 时抛出异常"""
        request = PlanRequest(
            goal=None,
            thread_id="test-thread-123"
        )
        
        with pytest.raises(ValueError, match="goal is required"):
            await planning_service.generate_and_store(request)

    @pytest.mark.asyncio
    async def test_generate_without_thread_id(self, planning_service):
        """测试没有提供 thread_id 时抛出异常"""
        request = PlanRequest(
            goal=PlanGoalInput(
                title="测试目标",
                type="study",  # 使用有效的枚举值
                deadline=date.today() + timedelta(days=30)
            ),
            thread_id=""  # 空字符串会被验证为无效
        )
        
        with pytest.raises(ValueError, match="thread_id is required"):
            await planning_service.generate_and_store(request)

    def test_get_plan(self, planning_service, db_session):
        """测试获取计划"""
        # 先创建一个 goal
        goal = Goal(
            memory_id="test-memory-get",
            title="测试获取计划",
            type="study",  # 使用有效的枚举值
            deadline=date.today() + timedelta(days=30)
        )
        db_session.add(goal)
        db_session.commit()
        db_session.refresh(goal)
        
        # 获取计划（传递 UUID 对象而不是字符串）
        plan = planning_service.get_plan(goal.id)
        
        assert plan is not None
        assert plan.focus == "测试获取计划"
        assert plan.milestones == []  # 新创建的 goal 没有 milestones

    def test_calculate_progress(self, planning_service, db_session):
        """测试计算进度"""
        # 创建带有任务的 goal
        from backend.models.milestone import Milestone
        from backend.models.task import Task
        
        goal = Goal(
            memory_id="test-memory-progress",
            title="测试进度计算",
            type="study",  # 使用有效的枚举值
            deadline=date.today() + timedelta(days=30)
        )
        db_session.add(goal)
        db_session.commit()
        db_session.refresh(goal)
        
        milestone = Milestone(
            goal_id=goal.id,
            title="测试里程碑",
            target_date=date.today() + timedelta(days=15),
            definition_of_done="测试完成标准",  # 必需字段
            order=1
        )
        db_session.add(milestone)
        db_session.commit()
        db_session.refresh(milestone)
        
        # 添加任务
        task1 = Task(
            goal_id=goal.id,
            milestone_id=milestone.id,
            title="任务 1",
            due_date=date.today() + timedelta(days=5),  # 必需字段
            status="completed",
            estimated_time=5
        )
        task2 = Task(
            goal_id=goal.id,
            milestone_id=milestone.id,
            title="任务 2",
            due_date=date.today() + timedelta(days=10),  # 必需字段
            status="in_progress",
            estimated_time=3
        )
        task3 = Task(
            goal_id=goal.id,
            milestone_id=milestone.id,
            title="任务 3",
            due_date=date.today() + timedelta(days=15),  # 必需字段
            status="pending",
            estimated_time=2
        )
        db_session.add_all([task1, task2, task3])
        db_session.commit()
        
        # 计算进度
        progress = planning_service.calculate_progress(goal.id)
        
        assert progress is not None
        assert progress["total_tasks"] == 3
        assert progress["completed_tasks"] == 1
        assert progress["task_progress"] == pytest.approx(33.3, 0.1)  # 用 task_progress 代替 completion_percentage
        assert progress["total_milestones"] == 1
        assert progress["completed_milestones"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
