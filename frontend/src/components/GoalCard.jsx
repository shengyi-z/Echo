// Card for the active goal with progress and next milestone.
function GoalCard() {
  return (
    <article className="dash-card">
      <header className="dash-card-header">
        <h2>Active goal</h2>
        <span className="pill">65%</span>
      </header>
      <p className="dash-card-subtitle">Goal: Finish the driving test by August</p>
      <div className="progress">
        <div className="progress-bar" style={{ width: '65%' }} />
      </div>
      <div className="dash-card-meta">
        <div>
          <span className="meta-label">Next milestone</span>
          <span className="meta-value">Complete Module 1 practice</span>
        </div>
        <div>
          <span className="meta-label">Nearest deadline</span>
          <span className="meta-value">Jun 12</span>
        </div>
      </div>
    </article>
  )
}

export default GoalCard
