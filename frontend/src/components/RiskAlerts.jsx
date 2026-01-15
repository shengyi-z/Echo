// Risk and dependency warnings.
function RiskAlerts({ alerts }) {
  if (!alerts || alerts.length === 0) {
    return (
      <article className="dash-card">
        <header className="dash-card-header">
          <h2>Risk alerts</h2>
          <span className="pill">0</span>
        </header>
        <p className="dash-card-subtitle">All clear! No risks detected.</p>
      </article>
    )
  }

  return (
    <article className="dash-card warning">
      <header className="dash-card-header">
        <h2>Risk alerts</h2>
        <span className="pill alert">{alerts.length}</span>
      </header>
      <div className="alert-list">
        {alerts.map((alert, index) => (
          <div key={index} className={`alert-item ${alert.severity}`}>
            {alert.message}
          </div>
        ))}
      </div>
    </article>
  )
}

export default RiskAlerts
