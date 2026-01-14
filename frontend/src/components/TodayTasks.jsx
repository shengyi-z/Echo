// Top 3 tasks for today.
function TodayTasks() {
  return (
    <article className="dash-card">
      <header className="dash-card-header">
        <h2>Today</h2>
        <span className="pill ghost">Top 3</span>
      </header>
      <ul className="dash-list">
        <li>
          <span className="list-dot" />
          Complete 30 minutes of Module 1 practice
        </li>
        <li>
          <span className="list-dot" />
          Prepare the application checklist
        </li>
        <li>
          <span className="list-dot" />
          Book a weekend driving session
        </li>
      </ul>
    </article>
  )
}

export default TodayTasks
