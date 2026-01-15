import { useState, useEffect } from 'react'
import GoalCard from './GoalCard'
import RiskAlerts from './RiskAlerts'
import TodayTasks from './TodayTasks'
import WeeklyTimeline from './WeeklyTimeline'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// 仪表盘视图：汇总当前进度。
function Dashboard({ onBack, showMenuButton, onToggleMenu }) {
  const [dashboardData, setDashboardData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE_URL}/api/dashboard/data`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      setDashboardData(data)
      setError(null)
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="dashboard">
        <header className="dashboard-header">
          <h1>Dashboard</h1>
          <p>Loading...</p>
        </header>
      </div>
    )
  }

  if (error) {
    return (
      <div className="dashboard">
        <header className="dashboard-header">
          <h1>Dashboard</h1>
          <p className="error">Error loading dashboard: {error}</p>
        </header>
      </div>
    )
  }

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

      <section className="dashboard-grid">
        <GoalCard data={dashboardData?.active_goal} />
        <TodayTasks tasks={dashboardData?.today_tasks || []} />
        <WeeklyTimeline />
        <RiskAlerts alerts={dashboardData?.risk_alerts || []} />
      </section>

      <div className="dashboard-footer">
        <button className="back-button" type="button" onClick={onBack}>
          Back
        </button>
      </div>
    </div>
  )
}

export default Dashboard
