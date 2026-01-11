// 风险提示卡片：展示逾期任务与潜在风险。
function RiskAlerts({ alerts = [], isLoading, error }) {
  // 加载态。
  if (isLoading) {
    return (
      <article className="dash-card warning">
        <header className="dash-card-header">
          <h2>Risks</h2>
          <span className="pill alert">...</span>
        </header>
        <p>Loading alerts...</p>
      </article>
    )
  }

  // 错误态。
  if (error) {
    return (
      <article className="dash-card warning">
        <header className="dash-card-header">
          <h2>Risks</h2>
          <span className="pill alert">!</span>
        </header>
        <p>Could not load alerts.</p>
      </article>
    )
  }

  // 空态。
  if (!alerts.length) {
    return (
      <article className="dash-card warning">
        <header className="dash-card-header">
          <h2>Risks</h2>
          <span className="pill alert">0</span>
        </header>
        <p>No overdue tasks.</p>
      </article>
    )
  }

  // 正常态。
  return (
    <article className="dash-card warning">
      <header className="dash-card-header">
        <h2>Risks</h2>
        <span className="pill alert">{alerts.length}</span>
      </header>
      <div className="alert-list">
        {alerts.map((alert) => (
          <div key={alert.id} className="alert-item">
            Overdue: {alert.title}
          </div>
        ))}
      </div>
    </article>
  )
}

export default RiskAlerts
