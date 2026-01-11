// Weekly milestones timeline.
function WeeklyTimeline() {
  return (
    <article className="dash-card">
      <header className="dash-card-header">
        <h2>本周关键节点</h2>
        <span className="pill ghost">Timeline</span>
      </header>
      <div className="timeline">
        <div className="timeline-row">
          <span className="timeline-date">Mon</span>
          <div>
            <p className="timeline-title">完成模拟考试</p>
            <p className="timeline-note">目标分数 90+</p>
          </div>
        </div>
        <div className="timeline-row">
          <span className="timeline-date">Wed</span>
          <div>
            <p className="timeline-title">提交报名材料</p>
            <p className="timeline-note">身份证 + 体检证明</p>
          </div>
        </div>
        <div className="timeline-row">
          <span className="timeline-date">Fri</span>
          <div>
            <p className="timeline-title">预约科目二练车</p>
            <p className="timeline-note">晚上 7 点之后</p>
          </div>
        </div>
      </div>
    </article>
  )
}

export default WeeklyTimeline
