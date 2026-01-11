// 日期格式化：兼容空值与无效日期。
const formatDate = (value) => {
  if (!value) return 'TBD'
  const date = new Date(value)
  if (Number.isNaN(date.valueOf())) return 'TBD'
  return date.toLocaleDateString()
}

// 主目标卡片：显示进度与最近里程碑/截止项。
function GoalCard({ goal, progressPercent = 0, nextMilestone, nextDeadline, isLoading, error }) {
  // 加载态。
  if (isLoading) {
    return (
      <article className="dash-card">
        <header className="dash-card-header">
          <h2>Active Goal</h2>
          <span className="pill">...</span>
        </header>
        <p className="dash-card-subtitle">Loading goal summary...</p>
        <div className="progress">
          <div className="progress-bar" style={{ width: '20%' }} />
        </div>
      </article>
    )
  }

  // 错误态。
  if (error) {
    return (
      <article className="dash-card">
        <header className="dash-card-header">
          <h2>Active Goal</h2>
          <span className="pill">!</span>
        </header>
        <p className="dash-card-subtitle">Could not load goal data.</p>
      </article>
    )
  }

  // 空态。
  if (!goal) {
    return (
      <article className="dash-card">
        <header className="dash-card-header">
          <h2>Active Goal</h2>
          <span className="pill">0%</span>
        </header>
        <p className="dash-card-subtitle">No goals yet. Create one to get started.</p>
      </article>
    )
  }

  // 正常态。
  return (
    <article className="dash-card">
      <header className="dash-card-header">
        <h2>Active Goal</h2>
        <span className="pill">{progressPercent}%</span>
      </header>
      <p className="dash-card-subtitle">Goal: {goal.title}</p>
      <div className="progress">
        <div className="progress-bar" style={{ width: `${progressPercent}%` }} />
      </div>
      <div className="dash-card-meta">
        <div>
          <span className="meta-label">Next milestone</span>
          <span className="meta-value">
            {nextMilestone ? nextMilestone.title : 'No upcoming milestones'}
          </span>
        </div>
        <div>
          <span className="meta-label">Nearest deadline</span>
          <span className="meta-value">
            {nextDeadline ? formatDate(nextDeadline.due_date) : 'No upcoming tasks'}
          </span>
        </div>
      </div>
    </article>
  )
}

export default GoalCard
