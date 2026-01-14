// Risk and dependency warnings.
function RiskAlerts() {
  return (
    <article className="dash-card warning">
      <header className="dash-card-header">
        <h2>Risk alerts</h2>
        <span className="pill alert">2</span>
      </header>
      <div className="alert-list">
        <div className="alert-item">
          Medical form is incomplete; application materials may be delayed.
        </div>
        <div className="alert-item">
          If you skip the practice test this week, next week may slip.
        </div>
      </div>
    </article>
  )
}

export default RiskAlerts
