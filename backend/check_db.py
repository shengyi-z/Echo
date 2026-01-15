"""
快速查看数据库内容的脚本
"""
from backend.core.db import SessionLocal
from backend.models.goal import Goal
from backend.models.milestone import Milestone
from backend.models.task import Task

def check_database():
    db = SessionLocal()
    try:
        # 查询所有目标
        goals = db.query(Goal).all()
        print(f"\n📊 数据库统计:")
        print(f"   Goals: {len(goals)}")
        
        for goal in goals:
            print(f"\n🎯 Goal: {goal.title}")
            print(f"   ID: {goal.id}")
            print(f"   Status: {goal.status}")
            print(f"   Milestones: {len(goal.milestones)}")
            
            for milestone in goal.milestones:
                print(f"      📍 {milestone.title} ({milestone.status})")
                print(f"         Tasks: {len(milestone.tasks)}")
                
                for task in milestone.tasks:
                    print(f"            ✅ {task.title} ({task.status})")
        
        # 统计总数
        total_milestones = db.query(Milestone).count()
        total_tasks = db.query(Task).count()
        
        print(f"\n📈 总计:")
        print(f"   Total Milestones: {total_milestones}")
        print(f"   Total Tasks: {total_tasks}")
        
    finally:
        db.close()

if __name__ == "__main__":
    check_database()
