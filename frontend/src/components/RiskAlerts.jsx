// Warning block for risks and dependencies.
function RiskAlerts() {
  return (
    <article className="dash-card warning">
      <header className="dash-card-header">
        <h2>风险提示</h2>
        <span className="pill alert">2</span>
      </header>
      <div className="alert-list">
        <div className="alert-item">
          体检表未完成，报名材料可能延迟。
        </div>
        <div className="alert-item">
          若本周未模拟考试，将影响下周预约。
        </div>
      </div>
    </article>
  )
}

export default RiskAlerts
