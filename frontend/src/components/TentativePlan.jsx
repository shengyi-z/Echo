import { useEffect, useState } from 'react'
import './TentativePlan.css'

function safeFormatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  if (Number.isNaN(d.getTime())) return String(dateStr)
  return d.toLocaleDateString()
}

function safeArray(x) {
  return Array.isArray(x) ? x : []
}

/**
 * TentativePlan Component
 * Displays the current plan with milestones, insights, and resources
 */
function TentativePlan({ plan, threadId }) {
  const [isConfirmed, setIsConfirmed] = useState(false)

  useEffect(() => {
    if (plan && threadId) {
      const confirmed = localStorage.getItem(`plan-confirmed-${threadId}`)
      setIsConfirmed(confirmed === 'true')
    }
  }, [plan, threadId])

  useEffect(() => {
    if (plan) {
      console.log('📋 TentativePlan received plan:', {
        goal_title: plan.goal_title,
        milestones: plan.milestones?.length,
        resources: plan.resources?.length,
      })
    }
  }, [plan])

  const handleConfirm = () => {
    if (!threadId || !plan) return
    localStorage.setItem(`plan-confirmed-${threadId}`, 'true')
    setIsConfirmed(true)
    window.dispatchEvent(new CustomEvent('planUpdated', { detail: { threadId } }))
    console.log('✅ Plan confirmed for thread:', threadId)
  }

  if (!plan) {
    return (
      <div className="tentative-plan empty">
        <div className="plan-empty-state">
          <div className="empty-icon">📋</div>
          <h3>No Plan Yet</h3>
          <p>Ask me to create a plan and it will appear here!</p>
        </div>
      </div>
    )
  }

  const milestones = safeArray(plan.milestones)
  const resources = safeArray(plan.resources)

  return (
    <div className="tentative-plan">
      <div className="plan-header">
        <div className="header-top">
          <h2>📊 {plan.goal_title || 'Your Plan'}</h2>
          <span className={`plan-badge ${isConfirmed ? 'confirmed' : 'pending'}`}>
            {isConfirmed ? 'Confirmed' : 'Pending'}
          </span>
        </div>

        {!isConfirmed && (
          <button className="confirm-plan-btn" onClick={handleConfirm}>
            ✓ Confirm Plan
          </button>
        )}

        {isConfirmed && (
          <p className="plan-hint confirmed">✅ This plan is confirmed and displayed in Dashboard</p>
        )}
      </div>

      <div className="plan-content">
        {/* ✅ 新 schema：response_to_user */}
        {plan.response_to_user && (
          <div className="plan-message">
            <p>{plan.response_to_user}</p>
          </div>
        )}

        {/* Milestones */}
        {milestones.length > 0 ? (
          <div className="plan-section">
            <div className="section-header">
              <span className="section-icon">🏆</span>
              <h3>Milestones</h3>
              <span className="count-badge">{milestones.length}</span>
            </div>

            <div className="milestone-list">
              {milestones.map((milestone, idx) => {
                const tasksInMilestone = safeArray(milestone?.tasks)
                return (
                  <div key={milestone?.id || `${milestone?.title || 'ms'}-${idx}`} className="milestone-item">
                    <div className="milestone-header">
                      <span className="milestone-title">{milestone?.title || 'Untitled Milestone'}</span>
                      {milestone?.target_date && (
                        <span className="milestone-date">{safeFormatDate(milestone.target_date)}</span>
                      )}
                    </div>

                    {milestone?.definition_of_done && (
                      <p className="milestone-description">{milestone.definition_of_done}</p>
                    )}

                    {/* ✅ 新：milestone 内嵌 tasks */}
                    {tasksInMilestone.length > 0 && (
                      <div className="task-list" style={{ marginTop: 10 }}>
                        {tasksInMilestone.map((task, tIdx) => (
                          <div key={task?.id || `${task?.title || 'task'}-${tIdx}`} className="task-item">
                            <div className="task-header">
                              <span className="task-title">{task?.title || 'Untitled Task'}</span>
                              {task?.priority && (
                                <span className={`priority-badge priority-${task.priority}`}>
                                  {task.priority}
                                </span>
                              )}
                            </div>
                            {task?.due_date && (
                              <div className="task-meta">
                                <span>Due: {safeFormatDate(task.due_date)}</span>
                              </div>
                            )}
                            {task?.estimated_time != null && (
                              <div className="task-meta">
                                <span>⏱️ {task.estimated_time}h</span>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        ) : (
          <div className="plan-section">
            <div className="section-header">
              <span className="section-icon">🧩</span>
              <h3>Milestones</h3>
            </div>
            <p className="section-text">
              暂时没有解析到 milestones（可能模型输出被截断）。你可以在下面 Insights 里查看原始输出，或让助手“重新生成更短 JSON”。
            </p>
          </div>
        )}

        {/* 兼容旧结构：plan.tasks（如果你某些接口还会给 tasks） */}
        {plan.tasks && safeArray(plan.tasks).length > 0 && (
          <div className="plan-section">
            <div className="section-header">
              <span className="section-icon">✅</span>
              <h3>Tasks</h3>
              <span className="count-badge">{safeArray(plan.tasks).length}</span>
            </div>
            <div className="task-list">
              {safeArray(plan.tasks).map((task, idx) => (
                <div key={task?.id || `${task?.title || 'task'}-${idx}`} className="task-item">
                  <div className="task-header">
                    <span className="task-title">{task?.title || 'Untitled Task'}</span>
                    {task?.priority && (
                      <span className={`priority-badge priority-${task.priority}`}>
                        {task.priority}
                      </span>
                    )}
                  </div>
                  {task?.due_date && (
                    <div className="task-meta">
                      <span>Due: {safeFormatDate(task.due_date)}</span>
                    </div>
                  )}
                  {task?.estimated_time != null && (
                    <div className="task-meta">
                      <span>⏱️ {task.estimated_time}h</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Insights */}
        {plan.insights && (
          <div className="plan-section">
            <div className="section-header">
              <span className="section-icon">💡</span>
              <h3>Insights</h3>
            </div>

            {plan.insights.overview && (
              <div className="insight-block">
                {/* ✅ partial plan 会把原始输出塞进 overview，这里用 pre 更好读 */}
                <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{plan.insights.overview}</pre>
              </div>
            )}

            {plan.insights.key_points && safeArray(plan.insights.key_points).length > 0 && (
              <div className="insight-block">
                <h4 className="insight-subtitle">Key Points</h4>
                <ul className="insight-list">
                  {safeArray(plan.insights.key_points).map((point, idx) => (
                    <li key={idx}>{point}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* ✅ 新 schema 字段：展示不展示都不影响，但这里放上更完整 */}
            {plan.insights.progression_guidelines && (
              <div className="insight-block">
                <h4 className="insight-subtitle">Progression</h4>
                <p>{plan.insights.progression_guidelines}</p>
              </div>
            )}
            {plan.insights.scientific_basis && (
              <div className="insight-block">
                <h4 className="insight-subtitle">Scientific Basis</h4>
                <p>{plan.insights.scientific_basis}</p>
              </div>
            )}
            {plan.insights.adjustments && (
              <div className="insight-block">
                <h4 className="insight-subtitle">Adjustments</h4>
                <p>{plan.insights.adjustments}</p>
              </div>
            )}
          </div>
        )}

        {/* Resources */}
        {resources.length > 0 && (
          <div className="plan-section">
            <div className="section-header">
              <span className="section-icon">🔗</span>
              <h3>Resources</h3>
              <span className="count-badge">{resources.length}</span>
            </div>
            <div className="resource-list">
              {resources.map((resource, idx) => (
                <a
                  key={idx}
                  href={resource.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="resource-link"
                >
                  <span className="resource-title">{resource.title || resource.url}</span>
                  {resource.category && (
                    <span className="resource-category">{resource.category}</span>
                  )}
                  <span className="external-icon">↗</span>
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default TentativePlan
