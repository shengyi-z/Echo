/**
 * Plan Storage Utilities
 * 管理 localStorage 中的 plan 数据
 */

/**
 * 保存 plan 到 localStorage
 * @param {Object} plan - PlanResponse 对象
 */
export const savePlan = (plan) => {
  if (!plan) {
    console.warn('⚠️  试图保存空的 plan')
    return
  }
  
  try {
    localStorage.setItem('currentPlan', JSON.stringify(plan))
    localStorage.setItem('planUpdatedAt', new Date().toISOString())
    console.log('✅ Plan 已保存到 localStorage')
    return true
  } catch (error) {
    console.error('❌ 保存 Plan 失败:', error)
    return false
  }
}

/**
 * 从 localStorage 读取当前的 plan
 * @returns {Object|null} PlanResponse 对象或 null
 */
export const getCurrentPlan = () => {
  try {
    const planStr = localStorage.getItem('currentPlan')
    if (!planStr) {
      console.log('ℹ️  localStorage 中没有保存的 plan')
      return null
    }
    
    const plan = JSON.parse(planStr)
    console.log('📊 从 localStorage 加载 Plan:', plan.focus || 'Untitled Plan')
    return plan
  } catch (error) {
    console.error('❌ 读取 Plan 失败:', error)
    return null
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
