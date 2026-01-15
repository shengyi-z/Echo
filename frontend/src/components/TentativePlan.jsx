import { useEffect, useState } from 'react'
import { getCurrentPlan } from '../utils/planStorage'
import './TentativePlan.css'

/**
 * TentativePlan Component
 * Displays the current plan with milestones, insights, and resources
 * Updates in real-time when plan changes
 */
function TentativePlan({ plan: externalPlan }) {
  const [plan, setPlan] = useState(externalPlan || null)

  // Load plan from localStorage or use external prop
  useEffect(() => {
    if (externalPlan) {
      setPlan(externalPlan)
    } else {
      const loadPlan = () => {
        const currentPlan = getCurrentPlan()
        setPlan(currentPlan)
      }
      loadPlan()
    }
  }, [externalPlan])

  // Listen for plan updates
  useEffect(() => {
    const handlePlanUpdate = () => {
      const currentPlan = getCurrentPlan()
      setPlan(currentPlan)
    }

    window.addEventListener('planUpdated', handlePlanUpdate)
    return () => window.removeEventListener('planUpdated', handlePlanUpdate)
  }, [])

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

  return (
    <div className="tentative-plan">
      <div className="plan-header">
        <h2>📊 Your Plan</h2>
        <span className="plan-badge">Active</span>
      </div>

      <div className="plan-content">
        {/* Focus */}
        {plan.focus && (
          <div className="plan-section">
            <div className="section-header">
              <span className="section-icon">🎯</span>
              <h3>Focus</h3>
            </div>
            <p className="section-text">{plan.focus}</p>
          </div>
        )}

        {/* Date */}
        {plan.date && (
          <div className="plan-meta">
            <span className="meta-label">📅 Date:</span>
            <span className="meta-value">{new Date(plan.date).toLocaleDateString()}</span>
          </div>
        )}

        {/* Message */}
        {plan.message && (
          <div className="plan-message">
            <p>{plan.message}</p>
          </div>
        )}

        {/* Milestones */}
        {plan.milestones && plan.milestones.length > 0 && (
          <div className="plan-section">
            <div className="section-header">
              <span className="section-icon">🏆</span>
              <h3>Milestones</h3>
              <span className="count-badge">{plan.milestones.length}</span>
            </div>
            <div className="milestone-list">
              {plan.milestones.map((milestone) => (
                <div key={milestone.id} className="milestone-item">
                  <div className="milestone-header">
                    <span className="milestone-title">{milestone.title}</span>
                    <span className="milestone-date">
                      {new Date(milestone.target_date).toLocaleDateString()}
                    </span>
                  </div>
                  <p className="milestone-description">{milestone.definition_of_done}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tasks */}
        {plan.tasks && plan.tasks.length > 0 && (
          <div className="plan-section">
            <div className="section-header">
              <span className="section-icon">✅</span>
              <h3>Tasks</h3>
              <span className="count-badge">{plan.tasks.length}</span>
            </div>
            <div className="task-list">
              {plan.tasks.map((task) => (
                <div key={task.id} className="task-item">
                  <div className="task-header">
                    <span className="task-title">{task.title}</span>
                    <span className={`priority-badge priority-${task.priority}`}>
                      {task.priority}
                    </span>
                  </div>
                  {task.due_date && (
                    <div className="task-meta">
                      <span>Due: {new Date(task.due_date).toLocaleDateString()}</span>
                    </div>
                  )}
                  {task.estimated_time && (
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
                <p>{plan.insights.overview}</p>
              </div>
            )}

            {plan.insights.key_points && plan.insights.key_points.length > 0 && (
              <div className="insight-block">
                <h4 className="insight-subtitle">Key Points</h4>
                <ul className="insight-list">
                  {plan.insights.key_points.map((point, idx) => (
                    <li key={idx}>{point}</li>
                  ))}
                </ul>
              </div>
            )}

            {plan.insights.precautions && plan.insights.precautions.length > 0 && (
              <div className="insight-block precautions">
                <h4 className="insight-subtitle">⚠️ Precautions</h4>
                <ul className="insight-list">
                  {plan.insights.precautions.map((precaution, idx) => (
                    <li key={idx}>{precaution}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Resources */}
        {plan.resources && plan.resources.length > 0 && (
          <div className="plan-section">
            <div className="section-header">
              <span className="section-icon">🔗</span>
              <h3>Resources</h3>
              <span className="count-badge">{plan.resources.length}</span>
            </div>
            <div className="resource-list">
              {plan.resources.map((resource, idx) => (
                <a
                  key={idx}
                  href={resource.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="resource-link"
                >
                  <span className="resource-title">
                    {resource.title || resource.url}
                  </span>
                  {resource.category && (
                    <span className="resource-category">{resource.category}</span>
                  )}
                  <span className="external-icon">↗</span>
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Warnings */}
        {plan.warnings && plan.warnings.length > 0 && (
          <div className="plan-section warnings">
            <div className="section-header">
              <span className="section-icon">⚠️</span>
              <h3>Warnings</h3>
            </div>
            <div className="warning-list">
              {plan.warnings.map((warning, idx) => (
                <div key={idx} className="warning-item">
                  {warning}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default TentativePlan
