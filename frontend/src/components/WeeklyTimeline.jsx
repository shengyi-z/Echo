// Weekly milestones timeline.
function WeeklyTimeline({ milestones }) {
  if (!milestones || milestones.length === 0) {
    return (
      <article className="dash-card">
        <header className="dash-card-header">
          <h2>Key milestones</h2>
          <span className="pill ghost">Timeline</span>
        </header>
        <p className="dash-card-subtitle">No milestones yet. Create a plan to see your timeline!</p>
      </article>
    )
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'TBD'
    const date = new Date(dateString)
    const options = { weekday: 'short', month: 'short', day: 'numeric' }
    return date.toLocaleDateString('en-US', options)
  }

  // Show first 3 milestones
  const displayMilestones = milestones.slice(0, 3)

  return (
    <article className="dash-card">
      <header className="dash-card-header">
        <h2>Key milestones</h2>
        <span className="pill ghost">Timeline</span>
      </header>
      <div className="timeline">
        {displayMilestones.map((milestone, index) => (
          <div key={milestone.id || index} className="timeline-row">
            <span className="timeline-date">{formatDate(milestone.target_date)}</span>
            <div>
              <p className="timeline-title">{milestone.title || 'Untitled Milestone'}</p>
              {milestone.definition_of_done && (
                <p className="timeline-note">{milestone.definition_of_done}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </article>
  )
}

export default WeeklyTimeline
