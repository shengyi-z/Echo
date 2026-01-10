"""
每日回顾系统 - 主动提醒和进度检查
Daily Digest - Proactive reminders and progress checks
"""
import asyncio
import json
from datetime import datetime, timedelta
from backboard import BackboardClient
from config.settings import settings


class DailyDigest:
    """每日摘要生成器"""
    
    def __init__(self, assistant_id: str, thread_id: str):
        self.client = BackboardClient(api_key=settings.BACKBOARD_API_KEY)
        self.assistant_id = assistant_id
        self.thread_id = thread_id
    
    async def generate_morning_briefing(self) -> str:
        """生成晨间简报"""
        
        today = datetime.now().strftime("%Y年%m月%d日")
        weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][datetime.now().weekday()]
        
        # 构造提示词
        prompt = f"""今天是{today} {weekday}，请生成我的每日简报：

1. **今日重点任务**
   - 检查是否有即将到来的截止日期（7天内）
   - 列出今天应该推进的里程碑
   
2. **进度回顾**
   - 回顾本周已完成的任务
   - 识别落后的项目并提出补救建议
   
3. **本周展望**
   - 本周剩余时间的关键任务
   - 需要提前准备的事项

4. **激励语**
   - 根据我的进度给一句鼓励的话

请简洁清晰，重点突出，用友好的语气。"""
        
        # 使用记忆功能获取历史信息
        response = await self.client.add_message(
            thread_id=self.thread_id,
            content=prompt,
            memory="Auto",
            stream=False
        )
        
        return response.content
    
    async def check_overdue_tasks(self) -> list:
        """检查逾期任务"""
        
        prompt = """请检查我所有目标中是否有逾期的里程碑或截止日期已过但未完成的任务。
        
如果有，请列出：
- 任务名称
- 原定截止日期
- 逾期天数
- 建议的补救措施

请以JSON格式返回：
{
  "overdue_tasks": [
    {
      "task": "任务名",
      "due_date": "YYYY-MM-DD",
      "days_overdue": 数字,
      "suggestion": "建议"
    }
  ]
}
"""
        
        response = await self.client.add_message(
            thread_id=self.thread_id,
            content=prompt,
            memory="Auto",
            stream=False
        )
        
        # 尝试解析JSON响应
        try:
            # 提取JSON部分
            content = response.content
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            else:
                json_str = content
            
            data = json.loads(json_str)
            return data.get("overdue_tasks", [])
        except:
            return []
    
    async def generate_weekly_summary(self) -> str:
        """生成周总结"""
        
        prompt = """请生成本周的总结报告：

1. **本周成就** 🎉
   - 完成了哪些里程碑
   - 有哪些进展值得庆祝
   
2. **遇到的挑战** 🤔
   - 哪些任务比预期困难
   - 是否需要调整计划
   
3. **下周计划** 📅
   - 下周的关键任务
   - 需要重点关注的目标
   
4. **总体进度** 📊
   - 各个长期目标的完成百分比
   - 预计完成时间是否需要调整

请用鼓励的语气，帮助我保持动力！"""
        
        response = await self.client.add_message(
            thread_id=self.thread_id,
            content=prompt,
            memory="Auto",
            stream=False
        )
        
        return response.content


class ReminderScheduler:
    """提醒调度器"""
    
    def __init__(self):
        self.reminders = []
    
    def add_reminder(self, reminder: dict):
        """添加提醒"""
        self.reminders.append(reminder)
    
    def get_today_reminders(self) -> list:
        """获取今日提醒"""
        today = datetime.now().date()
        
        today_reminders = []
        for reminder in self.reminders:
            reminder_date = datetime.strptime(reminder['date'], '%Y-%m-%d').date()
            
            if reminder_date == today:
                today_reminders.append(reminder)
        
        return today_reminders
    
    def get_upcoming_reminders(self, days: int = 7) -> list:
        """获取未来N天的提醒"""
        today = datetime.now().date()
        future_date = today + timedelta(days=days)
        
        upcoming = []
        for reminder in self.reminders:
            reminder_date = datetime.strptime(reminder['date'], '%Y-%m-%d').date()
            
            if today <= reminder_date <= future_date:
                days_until = (reminder_date - today).days
                reminder_copy = reminder.copy()
                reminder_copy['days_until'] = days_until
                upcoming.append(reminder_copy)
        
        return sorted(upcoming, key=lambda x: x['days_until'])


async def run_daily_digest(assistant_id: str, thread_id: str):
    """运行每日摘要（可以通过cron job定时执行）"""
    
    digest = DailyDigest(assistant_id, thread_id)
    
    print("="*60)
    print(f"📰 每日简报 - {datetime.now().strftime('%Y年%m月%d日 %H:%M')}")
    print("="*60)
    
    # 生成晨间简报
    briefing = await digest.generate_morning_briefing()
    print(f"\n{briefing}\n")
    
    # 检查逾期任务
    overdue = await digest.check_overdue_tasks()
    if overdue:
        print("\n⚠️  逾期任务提醒:")
        for task in overdue:
            print(f"\n  ❌ {task['task']}")
            print(f"     截止日期: {task['due_date']}")
            print(f"     已逾期: {task['days_overdue']} 天")
            print(f"     建议: {task['suggestion']}")
    
    print("\n" + "="*60)


async def run_weekly_summary(assistant_id: str, thread_id: str):
    """运行周总结（每周日晚上执行）"""
    
    digest = DailyDigest(assistant_id, thread_id)
    
    print("="*60)
    print(f"📊 本周总结 - {datetime.now().strftime('%Y年%m月%d日')}")
    print("="*60)
    
    summary = await digest.generate_weekly_summary()
    print(f"\n{summary}\n")
    
    print("="*60)


# 示例：设置定时任务
async def main():
    """示例：手动运行每日摘要"""
    
    # 这里使用你的助手ID和线程ID
    # 在实际使用中，这些应该从配置文件或数据库中读取
    assistant_id = "your_assistant_id_here"
    thread_id = "your_thread_id_here"
    
    # 生成每日简报
    await run_daily_digest(assistant_id, thread_id)
    
    # 或者生成周总结
    # await run_weekly_summary(assistant_id, thread_id)


if __name__ == "__main__":
    asyncio.run(main())