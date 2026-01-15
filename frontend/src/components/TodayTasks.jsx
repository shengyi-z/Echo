// Top 3 tasks for today.
function TodayTasks({ tasks }) {
  if (!tasks || tasks.length === 0) {
    return (
      <article className="dash-card">
        <header className="dash-card-header">
          <h2>Today</h2>
          <span className="pill ghost">Top 3</span>
        </header>
        <p className="dash-card-subtitle">No tasks for today. Great job staying on top of things!</p>
      </article>
    )
  }

  return (
    <article className="dash-card">
      <header className="dash-card-header">
        <h2>Today</h2>
        <span className="pill ghost">Top {tasks.length}</span>
      </header>
      <ul className="dash-list">
        {tasks.map((task) => (
          <li key={task.id}>
            <span className="list-dot" />
            {task.title}
          </li>
        ))}
      </ul>
    </article>
  )
}

export default TodayTasks
