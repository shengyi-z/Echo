// API 基础地址：支持环境变量覆盖。
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// 构建带查询参数的完整 URL。
const buildUrl = (path, params = {}) => {
  const url = new URL(path, API_BASE_URL)
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return
    url.searchParams.set(key, value)
  })
  return url.toString()
}

// 基础请求封装：统一错误处理并返回 JSON。
const fetchJson = async (path, params) => {
  const response = await fetch(buildUrl(path, params))
  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || `Request failed: ${response.status}`)
  }
  return response.json()
}

// 业务接口封装：Goals / Tasks 查询。
export const fetchGoals = (params) => fetchJson('/api/goals', params)
export const fetchTasks = (params) => fetchJson('/api/tasks', params)
