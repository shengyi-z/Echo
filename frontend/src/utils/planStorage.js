/**
 * Plan Storage Utilities
 * 管理 localStorage 中的 plan 数据 - 每个 thread_id 独立存储
 */

const PLANS_KEY = 'chatPlans' // 存储所有 thread 的 plans

/**
 * 保存 plan 到 localStorage (按 thread_id 存储)
 * @param {string} threadId - Thread ID
 * @param {Object} plan - PlanResponse 对象
 */
export const savePlan = (threadId, plan) => {
  if (!threadId) {
    console.warn('⚠️  缺少 threadId，无法保存 plan')
    return false
  }
  
  if (!plan) {
    console.warn('⚠️  试图保存空的 plan')
    return false
  }
  
  try {
    // 获取所有 plans
    const allPlans = getAllPlans()
    
    // 更新或添加当前 thread 的 plan
    allPlans[threadId] = {
      ...plan,
      updatedAt: new Date().toISOString()
    }
    
    localStorage.setItem(PLANS_KEY, JSON.stringify(allPlans))
    console.log(`✅ Plan 已保存到 localStorage (thread: ${threadId})`)
    
    // Trigger custom event for real-time updates in same window
    window.dispatchEvent(new CustomEvent('planUpdated', { detail: { threadId } }))
    
    return true
  } catch (error) {
    console.error('❌ 保存 Plan 失败:', error)
    return false
  }
}

/**
 * 从 localStorage 读取指定 thread 的 plan
 * @param {string} threadId - Thread ID
 * @returns {Object|null} PlanResponse 对象或 null
 */
export const getPlanByThreadId = (threadId) => {
  if (!threadId) {
    console.warn('⚠️  缺少 threadId')
    return null
  }
  
  try {
    const allPlans = getAllPlans()
    const plan = allPlans[threadId]
    
    if (!plan) {
      console.log(`ℹ️  Thread ${threadId} 没有保存的 plan`)
      return null
    }
    
    console.log(`📊 加载 Thread ${threadId} 的 Plan`)
    return plan
  } catch (error) {
    console.error('❌ 读取 Plan 失败:', error)
    return null
  }
}

/**
 * 获取所有 threads 的 plans
 * @returns {Object} { [threadId]: planData }
 */
export const getAllPlans = () => {
  try {
    const plansStr = localStorage.getItem(PLANS_KEY)
    if (!plansStr) {
      return {}
    }
    return JSON.parse(plansStr)
  } catch (error) {
    console.error('❌ 读取所有 Plans 失败:', error)
    return {}
  }
}

/**
 * 获取 plan 最后更新时间
 * @returns {Date|null} 更新时间或 null
 */
export const getPlanUpdatedAt = () => {
  try {
    const timestamp = localStorage.getItem('planUpdatedAt')
    return timestamp ? new Date(timestamp) : null
  } catch (error) {
    console.error('❌ 读取 Plan 更新时间失败:', error)
    return null
  }
}

/**
 * 清除保存的 plan
 */
export const clearPlan = () => {
  try {
    localStorage.removeItem('currentPlan')
    localStorage.removeItem('planUpdatedAt')
    console.log('🗑️  Plan 已从 localStorage 清除')
    return true
  } catch (error) {
    console.error('❌ 清除 Plan 失败:', error)
    return false
  }
}

/**
 * 检查是否有保存的 plan
 * @returns {boolean}
 */
export const hasPlan = () => {
  return localStorage.getItem('currentPlan') !== null
}
