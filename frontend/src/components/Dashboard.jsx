import GoalCard from './GoalCard'
import RiskAlerts from './RiskAlerts'
import TodayTasks from './TodayTasks'
import WeeklyTimeline from './WeeklyTimeline'

// Dashboard view that summarizes current progress.
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
          <button className="back-button" type="button" onClick={onBack}>
            Back
          </button>
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
    </div>
  )
}

export default Dashboard
