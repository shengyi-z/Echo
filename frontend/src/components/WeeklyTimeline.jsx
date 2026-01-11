// 周度里程碑时间线。
function WeeklyTimeline({ milestones = [], isLoading, error }) {
  // 加载态。
  if (isLoading) {
    return (
      <article className="dash-card">
        <header className="dash-card-header">
          <h2>Weekly timeline</h2>
          <span className="pill ghost">Timeline</span>
        </header>
        <p>Loading milestones...</p>
      </article>
    )
  }

  // 错误态。
  if (error) {
    return (
      <article className="dash-card">
        <header className="dash-card-header">
          <h2>Weekly timeline</h2>
          <span className="pill ghost">Timeline</span>
        </header>
        <p>Could not load milestones.</p>
      </article>
    )
  }

  // 空态。
  if (!milestones.length) {
    return (
      <article className="dash-card">
        <header className="dash-card-header">
          <h2>Weekly timeline</h2>
          <span className="pill ghost">Timeline</span>
        </header>
        <p>No milestones yet.</p>
      </article>
    )
  }

  // 正常态。
  return (
    <article className="dash-card">
      <header className="dash-card-header">
        <h2>Weekly timeline</h2>
        <span className="pill ghost">Timeline</span>
      </header>
      <div className="timeline">
        {milestones.map((milestone) => (
          <div key={milestone.id} className="timeline-row">
            <span className="timeline-date">
              {new Date(milestone.target_date).toLocaleDateString(undefined, {
                month: 'short',
                day: 'numeric',
              })}
            </span>
            <div>
              <p className="timeline-title">{milestone.title}</p>
              <p className="timeline-note">{milestone.definition_of_done}</p>
            </div>
          </div>
        ))}
      </div>
    </article>
  )
}

export default WeeklyTimeline
