// Weekly milestones timeline.
function WeeklyTimeline() {
  return (
    <article className="dash-card">
      <header className="dash-card-header">
        <h2>Key milestones</h2>
        <span className="pill ghost">Timeline</span>
      </header>
      <div className="timeline">
        <div className="timeline-row">
          <span className="timeline-date">Mon</span>
          <div>
            <p className="timeline-title">Finish mock test</p>
            <p className="timeline-note">Target score: 90+</p>
          </div>
        </div>
        <div className="timeline-row">
          <span className="timeline-date">Wed</span>
          <div>
            <p className="timeline-title">Submit application packet</p>
            <p className="timeline-note">ID + medical proof</p>
          </div>
        </div>
        <div className="timeline-row">
          <span className="timeline-date">Fri</span>
          <div>
            <p className="timeline-title">Book driving practice</p>
            <p className="timeline-note">After 7:00 PM</p>
          </div>
        </div>
      </div>
    </article>
  )
}

export default WeeklyTimeline
