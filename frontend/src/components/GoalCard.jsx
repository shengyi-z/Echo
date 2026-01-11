// Card for the active goal with progress and next milestone.
function GoalCard() {
  return (
    <article className="dash-card">
      <header className="dash-card-header">
        <h2>进行中的目标</h2>
        <span className="pill">65%</span>
      </header>
      <p className="dash-card-subtitle">目标：8 月前完成驾照考试</p>
      <div className="progress">
        <div className="progress-bar" style={{ width: '65%' }} />
      </div>
      <div className="dash-card-meta">
        <div>
          <span className="meta-label">下一里程碑</span>
          <span className="meta-value">完成科目一模拟</span>
        </div>
        <div>
          <span className="meta-label">最近 DDL</span>
          <span className="meta-value">6 月 12 日</span>
        </div>
      </div>
    </article>
  )
}

export default GoalCard
