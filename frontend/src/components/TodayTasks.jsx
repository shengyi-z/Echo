// Top 3 tasks for today.
function TodayTasks() {
  return (
    <article className="dash-card">
      <header className="dash-card-header">
        <h2>今日待办</h2>
        <span className="pill ghost">Top 3</span>
      </header>
      <ul className="dash-list">
        <li>
          <span className="list-dot" />
          完成 30 分钟科目一练习
        </li>
        <li>
          <span className="list-dot" />
          准备报名材料清单
        </li>
        <li>
          <span className="list-dot" />
          预约周末练车时间
        </li>
      </ul>
    </article>
  )
}

export default TodayTasks
