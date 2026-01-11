// 今日任务卡片：展示最近的待办清单。
function TodayTasks({ tasks = [], isLoading, error }) {
  // 加载态。
  if (isLoading) {
    return (
      <article className="dash-card">
        <header className="dash-card-header">
          <h2>Today</h2>
          <span className="pill ghost">Top 3</span>
        </header>
        <p>Loading tasks...</p>
      </article>
    )
  }

  // 错误态。
  if (error) {
    return (
      <article className="dash-card">
        <header className="dash-card-header">
          <h2>Today</h2>
          <span className="pill ghost">Top 3</span>
        </header>
        <p>Could not load tasks.</p>
      </article>
    )
  }

  // 空态。
  if (!tasks.length) {
    return (
      <article className="dash-card">
        <header className="dash-card-header">
          <h2>Today</h2>
          <span className="pill ghost">Top 3</span>
        </header>
        <p>No tasks due. Add a task to get started.</p>
      </article>
    )
  }

  // 正常态。
  return (
    <article className="dash-card">
      <header className="dash-card-header">
        <h2>Today</h2>
        <span className="pill ghost">Top 3</span>
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
