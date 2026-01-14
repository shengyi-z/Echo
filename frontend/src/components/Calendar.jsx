import { useMemo, useState } from 'react'

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
]
const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const EVENTS = [
  { date: '2026-01-06', title: 'Milestone: Research sprint' },
  { date: '2026-01-12', title: 'Review: Weekly sync' },
  { date: '2026-01-18', title: 'Milestone: Prototype ready' },
  { date: '2026-01-24', title: 'Launch prep checklist' },
]

// 日历页面：支持月/年视图与跨年跳转。
function Calendar({ onBack, showMenuButton, onToggleMenu }) {
  const [viewMode, setViewMode] = useState('month')
  const [selectedYear, setSelectedYear] = useState(2026)
  const [currentMonthIndex, setCurrentMonthIndex] = useState(0)

  // 打印当前日历视图。
  const handlePrint = () => {
    window.print()
  }

  // 过滤出当前年月的事件。
  const filteredEvents = useMemo(() => {
    return EVENTS.filter((event) => {
      const [year, month] = event.date.split('-').map(Number)
      return year === selectedYear && month === currentMonthIndex + 1
    })
  }, [selectedYear, currentMonthIndex])

  // 将事件映射到日期，便于快速查找。
  const eventsByDay = useMemo(() => {
    const map = new Map()
    filteredEvents.forEach((event) => {
      const day = Number(event.date.split('-')[2])
      map.set(day, event.title)
    })
    return map
  }, [filteredEvents])

  // 计算当月天数与首日偏移（周一为起点）。
  const daysInMonth = new Date(selectedYear, currentMonthIndex + 1, 0).getDate()
  const firstDay = new Date(selectedYear, currentMonthIndex, 1).getDay()
  const offset = (firstDay + 6) % 7
  const totalCells = offset + daysInMonth

  return (
    <div className="calendar">
      {/* 日历头部 */}
      <header className="calendar-header">
        {/* 顶部操作区 */}
        <div className="calendar-top">
          <div className="calendar-actions">
            {showMenuButton && (
              <button
                className="menu-button"
                type="button"
                onClick={onToggleMenu}
                aria-label="Toggle sidebar"
              >
                <span className="menu-icon" aria-hidden="true" />
              </button>
            )}
            <div className="calendar-toggle" role="tablist" aria-label="Calendar view">
              <button
                className={`calendar-toggle-button ${viewMode === 'month' ? 'active' : ''}`}
                type="button"
                onClick={() => setViewMode('month')}
                role="tab"
                aria-selected={viewMode === 'month'}
              >
                Month
              </button>
              <button
                className={`calendar-toggle-button ${viewMode === 'year' ? 'active' : ''}`}
                type="button"
                onClick={() => setViewMode('year')}
                role="tab"
                aria-selected={viewMode === 'year'}
              >
                Year
              </button>
            </div>
          </div>
          {/* 视图跳转控件 */}
          <div className="calendar-controls">
            <label className="calendar-field">
              <span>Year</span>
              <input
                type="number"
                min="1900"
                max="2100"
                value={selectedYear}
                onChange={(event) => setSelectedYear(Number(event.target.value || 0))}
              />
            </label>
            <label className="calendar-field">
              <span>Month</span>
              <select
                value={currentMonthIndex}
                onChange={(event) => {
                  setCurrentMonthIndex(Number(event.target.value))
                  setViewMode('month')
                }}
              >
                {MONTHS.map((month, index) => (
                  <option key={month} value={index}>{month}</option>
                ))}
              </select>
            </label>
          </div>
        </div>
        {/* 标题与打印按钮同行 */}
        <div className="calendar-title-row">
          <div className="calendar-title">
            <h1>Calendar</h1>
            <p>Plan milestones and see upcoming focus windows.</p>
          </div>
          <button className="ghost-button calendar-print" type="button" onClick={handlePrint}>
            Print
          </button>
        </div>
      </header>

      {/* 日历主体 */}
      <section className="calendar-content">
        {viewMode === 'month' ? (
          <div className="calendar-month">
            {/* 月视图头部 */}
            <div className="month-header">
              <h2>{MONTHS[currentMonthIndex]} {selectedYear}</h2>
              <span className="month-subtitle">Milestones and focus days</span>
            </div>
            {/* 星期标题 */}
            <div className="weekday-row">
              {WEEKDAYS.map((label) => (
                <span key={label} className="weekday">
                  {label}
                </span>
              ))}
            </div>
            {/* 月视图日期网格 */}
            <div className="month-grid">
              {Array.from({ length: totalCells }, (_, index) => {
                if (index < offset) {
                  return <div key={`empty-${index}`} className="day-card empty" />
                }
                const day = index - offset + 1
                const event = eventsByDay.get(day)
                return (
                  <div key={day} className={`day-card ${event ? 'has-event' : ''}`}>
                    <span className="day-number">{day}</span>
                    {event && <span className="day-event">{event}</span>}
                  </div>
                )
              })}
            </div>
          </div>
        ) : (
          <div className="calendar-year">
            {/* 年视图网格 */}
            <div className="year-grid">
              {MONTHS.map((month, index) => (
                <button
                  key={month}
                  type="button"
                  className="year-card"
                  onClick={() => {
                    setCurrentMonthIndex(index)
                    setViewMode('month')
                  }}
                >
                  <div className="year-card-header">
                    <span>{month}</span>
                    <span className="year-card-dot" />
                  </div>
                  <div className="year-card-grid">
                    {Array.from({ length: 12 }, (_, idx) => (
                      <span key={idx} className="year-card-cell" />
                    ))}
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* 侧边时间线 */}
        <aside className="calendar-timeline">
          <div className="timeline-header">
            <h3>Upcoming timeline</h3>
            <span>Next 30 days</span>
          </div>
          <div className="timeline-list">
            {filteredEvents.map((event) => (
              <div key={event.date} className="timeline-item">
                <div className="timeline-date-pill">{event.date}</div>
                <div className="timeline-info">
                  <strong>{event.title}</strong>
                  <span>Focus block - 2h</span>
                </div>
              </div>
            ))}
            {filteredEvents.length === 0 && (
              <div className="timeline-item">
                <div className="timeline-info">
                  <strong>No events scheduled</strong>
                  <span>Pick a different month or year.</span>
                </div>
              </div>
            )}
          </div>
        </aside>
      </section>

      {/* 底部操作区 */}
      <div className="calendar-footer">
        <button className="back-button" type="button" onClick={onBack}>
          Back
        </button>
      </div>
    </div>
  )
}

export default Calendar
