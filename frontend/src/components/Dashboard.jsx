import { useState, useEffect } from 'react'
import GoalCard from './GoalCard'
import RiskAlerts from './RiskAlerts'
import TodayTasks from './TodayTasks'
import WeeklyTimeline from './WeeklyTimeline'
import { getAllPlans } from '../utils/planStorage'

// 仪表盘视图：汇总当前进度。
function Dashboard({ onBack, showMenuButton, onToggleMenu }) {
  const [dashboardData, setDashboardData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadDashboardData()
    
    // Listen for plan updates
    const handlePlanUpdate = () => {
      console.log('📊 Dashboard: Plan updated, reloading data')
      loadDashboardData()
    }
    
    window.addEventListener('planUpdated', handlePlanUpdate)
    return () => window.removeEventListener('planUpdated', handlePlanUpdate)
  }, [])

  const loadDashboardData = () => {
    try {
      setLoading(true)
      
      // Get all plans from localStorage
      const allPlans = getAllPlans()
      const planEntries = Object.entries(allPlans)
      
      if (planEntries.length === 0) {
        setDashboardData({
          active_goal: null,
          today_tasks: [],
          risk_alerts: []
        })
        setError(null)
        setLoading(false)
        return
      }
      
      // Filter only confirmed plans
      const confirmedPlans = planEntries.filter(([threadId]) => {
        return localStorage.getItem(`plan-confirmed-${threadId}`) === 'true'
      })
      
      if (confirmedPlans.length === 0) {
        setDashboardData({
          active_goal: null,
          today_tasks: [],
          risk_alerts: [{
            message: 'No confirmed plans yet. Create and confirm a plan in chat to see it here.',
            severity: 'low'
          }]
        })
        setError(null)
        setLoading(false)
        return
      }
      
      // Use the most recently updated confirmed plan as active goal
      const sortedPlans = confirmedPlans.sort((a, b) => {
        const dateA = new Date(a[1].updatedAt || 0)
        const dateB = new Date(b[1].updatedAt || 0)
        return dateB - dateA
      })
      
      const [threadId, plan] = sortedPlans[0]
      
      // Transform plan data to dashboard format
      const transformedData = transformPlanToDashboard(plan, threadId)
      setDashboardData(transformedData)
      setError(null)
      
    } catch (err) {
      console.error('Failed to load dashboard data:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }
  
  // Transform localStorage plan data to dashboard format
  const transformPlanToDashboard = (plan, threadId) => {
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    
    // Extract goal title from plan
    const goalTitle = plan.goal_title || plan.response_to_user?.split('\n')[0] || 'My Goal'
    
    // Calculate progress (assume 0% for tentative plans)
    const progress = 0
    
    // Get next milestone (first milestone)
    const nextMilestone = plan.milestones && plan.milestones.length > 0
      ? {
          title: plan.milestones[0].title,
          target_date: plan.milestones[0].target_date
        }
      : null
    
    // Get nearest deadline (last milestone's date)
    const nearestDeadline = plan.milestones && plan.milestones.length > 0
      ? plan.milestones[plan.milestones.length - 1].target_date
      : null
    
    // Create active_goal object
    const activeGoal = {
      title: goalTitle,
      type: 'plan',
      deadline: nearestDeadline,
      progress_percentage: progress,
      next_milestone: nextMilestone,
      nearest_deadline: nextMilestone?.target_date
    }
    
    // Extract today's tasks from milestones
    const todayTasks = []
    if (plan.milestones && plan.milestones.length > 0) {
      // Take first 3 milestones as tasks
      plan.milestones.slice(0, 3).forEach((milestone, index) => {
        todayTasks.push({
          id: milestone.id || `milestone-${index}`,
          title: milestone.title,
          priority: index === 0 ? 'high' : index === 1 ? 'medium' : 'low',
          estimated_time: 2.0
        })
      })
    }
    
    // Generate risk alerts based on insights
    const riskAlerts = []
    if (plan.insights?.challenges && plan.insights.challenges.length > 0) {
      plan.insights.challenges.slice(0, 2).forEach(challenge => {
        riskAlerts.push({
          message: challenge,
          severity: 'medium'
        })
      })
    }
    
    // Add alert if no milestones
    if (!plan.milestones || plan.milestones.length === 0) {
      riskAlerts.push({
        message: 'No milestones defined yet. Break down your goal into smaller steps.',
        severity: 'low'
      })
    }
    
    return {
      active_goal: activeGoal,
      today_tasks: todayTasks,
      risk_alerts: riskAlerts,
      milestones: plan.milestones || []
    }
  }

  if (loading) {
    return (
      <div className="dashboard">
        <header className="dashboard-header">
          <div className="dashboard-actions">
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
          </div>
          <div>
            <h1>Dashboard</h1>
            <p>Loading your plans...</p>
          </div>
        </header>
      </div>
    )
  }

  if (error) {
    return (
      <div className="dashboard">
        <header className="dashboard-header">
          <div className="dashboard-actions">
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
          </div>
          <div>
            <h1>Dashboard</h1>
            <p className="error">Error: {error}</p>
          </div>
        </header>
      </div>
    )
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="dashboard-actions">
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
        </div>
        <div>
          <h1>Dashboard</h1>
          <p>Stay on top of what matters this week.</p>
        </div>
      </header>

      <section className="dashboard-grid">
        <GoalCard data={dashboardData?.active_goal} />
        <TodayTasks tasks={dashboardData?.today_tasks || []} />
        <WeeklyTimeline milestones={dashboardData?.milestones || []} />
        <RiskAlerts alerts={dashboardData?.risk_alerts || []} />
      </section>

      <div className="dashboard-footer">
        <button className="back-button" type="button" onClick={onBack}>
          Back
        </button>
      </div>
    </div>
  )
}

export default Dashboard
