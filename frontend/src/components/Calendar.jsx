import { useMemo, useState, useEffect } from 'react'
import { getAllPlans } from '../utils/planStorage'

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
]
const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

// 日历页面：支持月/年视图与跨年跳转。
function Calendar({ onBack, showMenuButton, onToggleMenu }) {
  const [viewMode, setViewMode] = useState('month')
  const [selectedYear, setSelectedYear] = useState(2026)
  const [currentMonthIndex, setCurrentMonthIndex] = useState(0)
  const [events, setEvents] = useState([])

  // Load milestones from confirmed plans
  useEffect(() => {
    loadMilestones()
    
    // Listen for plan updates
    const handlePlanUpdate = () => {
      console.log('📅 Calendar: Plan updated, reloading milestones')
      loadMilestones()
    }
    
    window.addEventListener('planUpdated', handlePlanUpdate)
    return () => window.removeEventListener('planUpdated', handlePlanUpdate)
  }, [])

  const loadMilestones = () => {
    try {
      const allPlans = getAllPlans()
      const planEntries = Object.entries(allPlans)
      
      // Filter only confirmed plans
      const confirmedPlans = planEntries.filter(([threadId]) => {
        return localStorage.getItem(`plan-confirmed-${threadId}`) === 'true'
      })
      
      // Extract all milestones from confirmed plans
      const milestoneEvents = []
      confirmedPlans.forEach(([threadId, plan]) => {
        if (plan.milestones && Array.isArray(plan.milestones)) {
          plan.milestones.forEach(milestone => {
            if (milestone.target_date) {
              milestoneEvents.push({
                date: milestone.target_date,
                title: milestone.title || 'Untitled Milestone',
                description: milestone.definition_of_done || '',
                planTitle: plan.goal_title || 'Goal'
              })
            }
          })
        }
      })
      
      // Sort by date
      milestoneEvents.sort((a, b) => new Date(a.date) - new Date(b.date))
      
      setEvents(milestoneEvents)
      console.log('📅 Loaded milestones:', milestoneEvents.length)
    } catch (err) {
      console.error('Failed to load milestones:', err)
      setEvents([])
    }
  }

  // 打印当前日历视图。
  const handlePrint = () => {
    window.print()
  }

  // 生成并下载日历文件（ICS）。
  const handleDownload = () => {
    const pad = (value) => String(value).padStart(2, '0')
    const lines = [
      'BEGIN:VCALENDAR',
      'VERSION:2.0',
      'PRODID:-//Echo//Calendar Export//EN',
    ]

    events.forEach((event, index) => {
      const [year, month, day] = event.date.split('-')
      const stamp = `${year}${month}${day}T090000Z`
      const uid = `echo-${year}${month}${day}-${index}@echo`
      lines.push(
        'BEGIN:VEVENT',
        `UID:${uid}`,
        `DTSTAMP:${stamp}`,
        `DTSTART:${year}${month}${day}T090000Z`,
        `DTEND:${year}${month}${day}T100000Z`,
        `SUMMARY:${event.title}`,
        event.description ? `DESCRIPTION:${event.description}` : '',
        'END:VEVENT'
      )
    })

    lines.push('END:VCALENDAR')
    const blob = new Blob([lines.join('\n')], { type: 'text/calendar;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `calendar-${selectedYear}.ics`
    anchor.click()
    URL.revokeObjectURL(url)
  }

  // 过滤出当前年月的事件。
  const filteredEvents = useMemo(() => {
    return events.filter((event) => {
      const [year, month] = event.date.split('-').map(Number)
      return year === selectedYear && month === currentMonthIndex + 1
    })
  }, [events, selectedYear, currentMonthIndex])

  // 将事件映射到日期，便于快速查找。
  const eventsByDay = useMemo(() => {
    const map = new Map()
    filteredEvents.forEach((event) => {
      const day = Number(event.date.split('-')[2])
      if (!map.has(day)) {
        map.set(day, [])
      }
      map.get(day).push(event)
    })
    return map
  }, [filteredEvents])

  // 计算接下来30天的milestones（用于侧边timeline）
  const upcomingEvents = useMemo(() => {
    const now = new Date()
    const thirtyDaysLater = new Date(now)
    thirtyDaysLater.setDate(thirtyDaysLater.getDate() + 30)
    
    return events.filter(event => {
      const eventDate = new Date(event.date)
      return eventDate >= now && eventDate <= thirtyDaysLater
    }).slice(0, 10) // 最多显示10个
  }, [events])

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
        {/* 标题与操作按钮同行 */}
        <div className="calendar-title-row">
          <div className="calendar-title">
            <h1>Calendar</h1>
            <p>Plan milestones and see upcoming focus windows.</p>
          </div>
          <div className="calendar-cta">
            <button className="ghost-button calendar-cta-button" type="button" onClick={handlePrint}>
              Print
            </button>
            <button className="ghost-button calendar-cta-button" type="button" onClick={handleDownload}>
              Download
            </button>
          </div>
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
                const dayEvents = eventsByDay.get(day) || []
                return (
                  <div key={day} className={`day-card ${dayEvents.length > 0 ? 'has-event' : ''}`}>
                    <span className="day-number">{day}</span>
                    {dayEvents.map((event, idx) => (
                      <span key={idx} className="day-event" title={event.description}>
                        {event.title}
                      </span>
                    ))}
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
            {upcomingEvents.map((event, index) => {
              const eventDate = new Date(event.date)
              const daysUntil = Math.ceil((eventDate - new Date()) / (1000 * 60 * 60 * 24))
              return (
                <div key={`${event.date}-${index}`} className="timeline-item">
                  <div className="timeline-date-pill">{event.date}</div>
                  <div className="timeline-info">
                    <strong>{event.title}</strong>
                    <span>
                      {daysUntil === 0 ? 'Today' : daysUntil === 1 ? 'Tomorrow' : `In ${daysUntil} days`}
                      {event.planTitle && ` • ${event.planTitle}`}
                    </span>
                  </div>
                </div>
              )
            })}
            {upcomingEvents.length === 0 && (
              <div className="timeline-item">
                <div className="timeline-info">
                  <strong>No upcoming milestones</strong>
                  <span>Create a plan to see your timeline!</span>
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
