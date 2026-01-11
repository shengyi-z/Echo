import { useEffect, useState } from 'react'
import { fetchGoals, fetchTasks } from '../api'
import GoalCard from './GoalCard'
import RiskAlerts from './RiskAlerts'
import TodayTasks from './TodayTasks'
import WeeklyTimeline from './WeeklyTimeline'

// Dashboard 视图：加载目标与任务数据并分发给子组件。
function Dashboard({ onBack, showMenuButton, onToggleMenu }) {
  // 数据状态：目标、任务与风险提醒。
  const [goals, setGoals] = useState([])
  const [tasks, setTasks] = useState([])
  const [overdueTasks, setOverdueTasks] = useState([])
  // UI 状态：加载/错误。
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  // 首次进入时拉取所需数据。
  useEffect(() => {
    let isMounted = true
    const today = new Date().toISOString().slice(0, 10)

    const loadData = async () => {
      setIsLoading(true)
      setError(null)
      try {
        const [goalsData, tasksData, overdueData] = await Promise.all([
          fetchGoals({ include_children: true }),
          fetchTasks({ outstanding_only: true, order_by: 'due_date', order_dir: 'asc' }),
          fetchTasks({ outstanding_only: true, due_before: today }),
        ])
        if (!isMounted) return
        setGoals(goalsData)
        setTasks(tasksData)
        setOverdueTasks(overdueData)
      } catch (err) {
        if (!isMounted) return
        setError(err.message || 'Failed to load dashboard data.')
      } finally {
        if (!isMounted) return
        setIsLoading(false)
      }
    }

    loadData()
    return () => {
      isMounted = false
    }
  }, [])

  // 业务派生数据：当前目标、进度、里程碑、最近截止任务。
  const activeGoal = goals[0] || null
  const goalTasks = activeGoal?.tasks || []
  const completedTasks = goalTasks.filter((task) => task.status === 'completed').length
  const totalTasks = goalTasks.length
  const progressPercent = totalTasks ? Math.round((completedTasks / totalTasks) * 100) : 0

  const nextMilestone = activeGoal?.milestones
    ? [...activeGoal.milestones]
        .filter((milestone) => milestone.status !== 'completed')
        .sort((a, b) => new Date(a.target_date) - new Date(b.target_date))[0]
    : null

  const nextDeadline = goalTasks
    .filter((task) => task.status !== 'completed')
    .sort((a, b) => new Date(a.due_date) - new Date(b.due_date))[0]

  const topTasks = tasks.slice(0, 3)
  const timelineItems = (activeGoal?.milestones || []).slice(0, 3)

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="dashboard-actions">
          {showMenuButton && (
            <button
              className="menu-button"
              type="button"
              onClick={onToggleMenu}
              aria-label="Toggle sidebar"
            >
              <span className="menu-icon" aria-hidden="true" />
            </button>
          )}
        </div>
        <div>
          <h1>Dashboard</h1>
          <p>Stay on top of what matters this week.</p>
        </div>
      </header>

      {isLoading ? (
        <section className="dashboard-grid">
          <GoalCard isLoading />
          <TodayTasks isLoading />
          <WeeklyTimeline isLoading />
          <RiskAlerts isLoading />
        </section>
      ) : (
        <section className="dashboard-grid">
          <GoalCard
            goal={activeGoal}
            progressPercent={progressPercent}
            nextMilestone={nextMilestone}
            nextDeadline={nextDeadline}
            error={error}
          />
          <TodayTasks tasks={topTasks} error={error} />
          <WeeklyTimeline milestones={timelineItems} error={error} />
          <RiskAlerts alerts={overdueTasks} error={error} />
        </section>
      )}

      <div className="dashboard-footer">
        <button className="back-button" type="button" onClick={onBack}>
          Back
        </button>
      </div>
    </div>
  )
}

export default Dashboard
