import GoalCard from './GoalCard'
import RiskAlerts from './RiskAlerts'
import TodayTasks from './TodayTasks'
import WeeklyTimeline from './WeeklyTimeline'

// 仪表盘视图：汇总当前进度。
function Dashboard({ onBack, showMenuButton, onToggleMenu }) {
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
        <GoalCard />
        <TodayTasks />
        <WeeklyTimeline />
        <RiskAlerts />
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
