// Card for the active goal with progress and next milestone.
function GoalCard({ data }) {
  if (!data) {
    return (
      <article className="dash-card">
        <header className="dash-card-header">
          <h2>Active goal</h2>
        </header>
        <p className="dash-card-subtitle">No active goal. Start by creating a plan!</p>
      </article>
    )
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  return (
    <article className="dash-card">
      <header className="dash-card-header">
        <h2>Active goal</h2>
        <span className="pill">{data.progress_percentage}%</span>
      </header>
      <p className="dash-card-subtitle">Goal: {data.title}</p>
      <div className="progress">
        <div className="progress-bar" style={{ width: `${data.progress_percentage}%` }} />
      </div>
      <div className="dash-card-meta">
        {data.next_milestone && (
          <div>
            <span className="meta-label">Next milestone</span>
            <span className="meta-value">{data.next_milestone.title}</span>
          </div>
        )}
        {data.nearest_deadline && (
          <div>
            <span className="meta-label">Nearest deadline</span>
            <span className="meta-value">{formatDate(data.nearest_deadline)}</span>
          </div>
        )}
      </div>
    </article>
  )
}

export default GoalCard
