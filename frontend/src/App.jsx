import { useEffect, useState, useRef } from 'react'
import ChatInput from './components/ChatInput'
import ChatMessage from './components/ChatMessage'
import Calendar from './components/Calendar'
import Dashboard from './components/Dashboard'
import Settings from './components/Settings'
import Sidebar from './components/Sidebar'
import TentativePlan from './components/TentativePlan'
import { savePlan, getPlanByThreadId } from './utils/planStorage'
import './App.css'

const API_BASE_URL = 'http://localhost:8000'

const initialMessages = [
  {
    id: 'm1',
    role: 'assistant',
    content:
      'Hey! Tell me the goal you want to tackle first, and I will break it into steps.',
    time: '09:10',
  },
]

/**
 * =====================================================
 * ✅ 新增：Plan JSON 容错提取工具（不影响你原本 UI）
 * =====================================================
 */

/** 判断文本“像不像计划输出”：用于 JSON 解析失败时仍显示 partial plan */
function looksLikePlanText(text) {
  if (!text) return false
  const t = String(text)
  return /```json|milestones|definition_of_done|response_to_user|goal_title|resources|insights/i.test(
    t
  )
}

/** 尝试从 ```json ... ``` 中取出 JSON 字符串 */
function extractJsonFromFence(content) {
  if (!content) return null
  const match = String(content).match(/```json\s*([\s\S]*?)\s*```/i)
  if (!match) return null
  return match[1]?.trim() || null
}

/**
 * 从全文中提取“第一个完整 JSON 对象”
 * - 通过括号配对计数（支持字符串状态，避免字符串里的 { } 干扰）
 */
function extractFirstJSONObject(content) {
  if (!content) return null
  const s = String(content)
  const start = s.indexOf('{')
  if (start === -1) return null

  let inString = false
  let escape = false
  let depth = 0

  for (let i = start; i < s.length; i++) {
    const ch = s[i]

    // 处理转义
    if (escape) {
      escape = false
      continue
    }
    if (ch === '\\') {
      if (inString) escape = true
      continue
    }

    // 处理字符串引号
    if (ch === '"') {
      inString = !inString
      continue
    }

    // 非字符串状态才计括号
    if (!inString) {
      if (ch === '{') depth++
      if (ch === '}') depth--
      if (depth === 0) {
        return s.slice(start, i + 1).trim()
      }
    }
  }

  // 没闭合（通常是模型输出被截断）
  return null
}

/**
 * 尝试从模型输出解析出 planData（带 fallback）
 * 返回：
 * - planData: 给 TentativePlan 用（就算解析失败也能给 partial）
 * - displayContent: 聊天窗口展示内容（优先 response_to_user）
 * - parseOk: 是否成功得到结构化 plan
 */
function parsePlanFromModelContent(rawContent) {
  const content = String(rawContent ?? '')
  let displayContent = content

  // 1) 优先：```json fence
  const fenced = extractJsonFromFence(content)
  if (fenced) {
    try {
      const parsed = JSON.parse(fenced)
      if (parsed?.response_to_user && parsed?.milestones) {
        displayContent = parsed.response_to_user
        return {
          parseOk: true,
          displayContent,
          planData: {
            response_to_user: parsed.response_to_user,
            goal_title: parsed.goal_title || '',
            milestones: Array.isArray(parsed.milestones) ? parsed.milestones : [],
            insights: parsed.insights || null,
            resources: Array.isArray(parsed.resources) ? parsed.resources : [],
          },
        }
      }
    } catch (e) {
      console.log('⚠️ fence JSON 解析失败，将尝试其它提取方式:', e.message)
    }
  }

  // 2) 次选：全文第一个完整 JSON 对象
  const objStr = extractFirstJSONObject(content)
  if (objStr) {
    try {
      const parsed = JSON.parse(objStr)
      if (parsed?.response_to_user && parsed?.milestones) {
        displayContent = parsed.response_to_user
        return {
          parseOk: true,
          displayContent,
          planData: {
            response_to_user: parsed.response_to_user,
            goal_title: parsed.goal_title || '',
            milestones: Array.isArray(parsed.milestones) ? parsed.milestones : [],
            insights: parsed.insights || null,
            resources: Array.isArray(parsed.resources) ? parsed.resources : [],
          },
        }
      }
    } catch (e) {
      console.log('⚠️ 全文 JSON 解析失败（可能被截断/混入文本）:', e.message)
    }
  }

  // 3) fallback：解析失败但“看起来像 plan”，生成 partial plan 让右侧不空
  if (looksLikePlanText(content)) {
    const partial = {
      response_to_user:
        '我收到一个计划草稿，但结构化 JSON 解析失败（可能被截断）。你仍然可以先查看原始内容，然后让我重新生成一次更短的 JSON 版本。',
      goal_title: '（计划草稿 / 未完全解析）',
      milestones: [],
      insights: {
        // ✅ 原文放进 overview，方便你 debug + 用户也能看到内容
        overview: `【原始输出（用于排查/人工查看）】\n\n${content}`,
        key_points: [],
        progression_guidelines: '',
        scientific_basis: '',
        adjustments: '',
      },
      resources: [],
    }
    return { parseOk: false, displayContent, planData: partial }
  }

  // 4) 完全不是 plan：不显示 plan panel
  return { parseOk: false, displayContent, planData: null }
}

function App() {
  const [chatSessions, setChatSessions] = useState([])
  const [currentThreadId, setCurrentThreadId] = useState(null)
  const [messages, setMessages] = useState(initialMessages)
  const [draft, setDraft] = useState('')
  const [activeView, setActiveView] = useState('chat')
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [isSmallScreen, setIsSmallScreen] = useState(false)
  const [assistantId, setAssistantId] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isInitialized, setIsInitialized] = useState(false)
  const [isEditingTitle, setIsEditingTitle] = useState(false)
  const [editTitleValue, setEditTitleValue] = useState('')
  const [chatOrder, setChatOrder] = useState([])
  const [chatSearch, setChatSearch] = useState('')
  const [showPlan, setShowPlan] = useState(false)
  const [currentPlan, setCurrentPlan] = useState(null)
  const chatScrollRef = useRef(null)

  // Auto-scroll to latest message
  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight
    }
  }, [messages])

  // Load plan for current thread
  useEffect(() => {
    if (currentThreadId) {
      const plan = getPlanByThreadId(currentThreadId)
      if (plan) {
        setCurrentPlan(plan)
        setShowPlan(true)
      } else {
        setCurrentPlan(null)
        setShowPlan(false)
      }
    }
  }, [currentThreadId])

  // Listen for plan updates from localStorage
  useEffect(() => {
    const handlePlanUpdate = (event) => {
      // 只更新当前 thread 的 plan
      const { threadId } = event.detail || {}
      if (threadId && threadId === currentThreadId) {
        const plan = getPlanByThreadId(currentThreadId)
        setCurrentPlan(plan)
        if (plan && !showPlan) {
          setShowPlan(true)
        }
      }
    }

    // Custom event for same-window updates
    window.addEventListener('planUpdated', handlePlanUpdate)

    return () => {
      window.removeEventListener('planUpdated', handlePlanUpdate)
    }
  }, [currentThreadId, showPlan])

  // Initialize or load saved chat sessions on user login
  useEffect(() => {
    const savedSessions = localStorage.getItem('chatSessions')
    const savedThreadId = localStorage.getItem('currentThreadId')
    const savedAssistantId = localStorage.getItem('assistantId')

    if (savedSessions && savedThreadId && savedAssistantId) {
      const sessions = JSON.parse(savedSessions)
      setChatSessions(sessions)
      setCurrentThreadId(savedThreadId)
      setAssistantId(savedAssistantId)
      setIsInitialized(true)

      const currentSession = sessions.find((s) => s.thread_id === savedThreadId)
      if (currentSession) {
        setMessages(currentSession.messages)
      }

      console.log('✅ Loaded saved sessions from localStorage')
      return
    }

    const initializeChat = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/chat/init`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({}),
        })

        if (!response.ok) {
          throw new Error('Failed to initialize')
        }

        const data = await response.json()
        setCurrentThreadId(data.thread_id)
        setAssistantId(data.assistant_id)
        setIsInitialized(true)

        const newSession = {
          id: data.thread_id,
          thread_id: data.thread_id,
          title: 'New Chat',
          preview: 'Start your first conversation...',
          messages: [...initialMessages],
          isFirstMessage: true,
        }
        setChatSessions([newSession])

        localStorage.setItem('chatSessions', JSON.stringify([newSession]))
        localStorage.setItem('currentThreadId', data.thread_id)
        localStorage.setItem('assistantId', data.assistant_id)

        console.log('✅ Chat initialized:', data.message)
      } catch (error) {
        console.error('❌ Initialization failed:', error)
      }
    }

    initializeChat()
  }, [])

  // Save chat history to localStorage
  useEffect(() => {
    if (chatSessions.length > 0 && isInitialized) {
      localStorage.setItem('chatSessions', JSON.stringify(chatSessions))
    }
  }, [chatSessions, isInitialized])

  useEffect(() => {
    const mediaQuery = window.matchMedia('(max-width: 640px)')
    const syncState = () => {
      setIsSmallScreen(mediaQuery.matches)
      if (!mediaQuery.matches) {
        setIsSidebarOpen(false)
      }
    }
    syncState()
    mediaQuery.addEventListener('change', syncState)
    return () => mediaQuery.removeEventListener('change', syncState)
  }, [])

  // Generate unique 'New Chat' title
  const getUniqueNewChatTitle = () => {
    const existingTitles = chatSessions.map((s) => s.title)
    let counter = 1
    let title = 'New Chat'

    // If 'New Chat' already exists, try 'New Chat 1', 'New Chat 2', etc.
    while (existingTitles.includes(title)) {
      title = `New Chat ${counter}`
      counter++
    }

    return title
  }

  // Create new chat
  const handleNewChat = async () => {
    try {
      console.log('🆕 Creating new chat...')
      console.log('Current sessions:', chatSessions.map((s) => s.title))

      const uniqueTitle = getUniqueNewChatTitle()
      console.log('Generated unique title:', uniqueTitle)

      const response = await fetch(`${API_BASE_URL}/api/chat/new`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: uniqueTitle,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to create new chat')
      }

      const data = await response.json()
      console.log('✅ New chat created:', data)

      const newSession = {
        id: data.thread_id,
        thread_id: data.thread_id,
        title: uniqueTitle,
        preview: 'Start a new conversation...',
        messages: [...initialMessages],
        isFirstMessage: true,
      }

      setChatSessions((prev) => {
        const updated = [...prev, newSession]
        console.log('Updated sessions:', updated.map((s) => s.title))
        return updated
      })
      setCurrentThreadId(data.thread_id)
      setMessages([...initialMessages])
      setActiveView('chat')

      localStorage.setItem('currentThreadId', data.thread_id)

      console.log('📝 Chat sessions updated')
    } catch (error) {
      console.error('❌ Failed to create new chat:', error.message)
    }
  }

  // Switch chat
  const handleSelectChat = (chatId) => {
    const session = chatSessions.find((s) => s.id === chatId)
    if (session) {
      setCurrentThreadId(session.thread_id)
      setMessages(session.messages)
      setActiveView('chat')
      localStorage.setItem('currentThreadId', session.thread_id)
      if (isSmallScreen) {
        setIsSidebarOpen(false)
      }
    }
  }

  // Update chat title
  const handleUpdateTitle = async (threadId, newTitle) => {
    if (!newTitle.trim()) return

    try {
      await fetch(`${API_BASE_URL}/api/chat/update-title`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          thread_id: threadId,
          title: newTitle.trim(),
        }),
      })

      setChatSessions((prev) =>
        prev.map((session) =>
          session.thread_id === threadId ? { ...session, title: newTitle.trim() } : session
        )
      )

      console.log('✅ Title updated:', newTitle)
    } catch (error) {
      console.error('❌ Failed to update title:', error)
    }
  }

  // Start editing title (Chat Area)
  const handleStartEditTitle = () => {
    const currentSession = chatSessions.find((s) => s.thread_id === currentThreadId)
    if (currentSession) {
      setEditTitleValue(currentSession.title)
      setIsEditingTitle(true)
    }
  }

  // Save title edit (Chat Area)
  const handleSaveTitleEdit = () => {
    if (editTitleValue.trim() && currentThreadId) {
      handleUpdateTitle(currentThreadId, editTitleValue.trim())
    }
    setIsEditingTitle(false)
  }

  // Cancel title edit (Chat Area)
  const handleCancelTitleEdit = () => {
    setIsEditingTitle(false)
    setEditTitleValue('')
  }

  // Update current chat messages
  const updateCurrentSessionMessages = (newMessages, suggestedTitle = null) => {
    setChatSessions((prev) =>
      prev.map((session) => {
        if (session.thread_id === currentThreadId) {
          const updates = {
            messages: newMessages,
            preview:
              newMessages[newMessages.length - 1]?.content?.slice(0, 30) + '...' ||
              'No messages',
            isFirstMessage: false,
          }

          // If suggested title exists and current title is still 'New Chat' series, auto-update
          if (suggestedTitle && session.title.match(/^New Chat( \d+)?$/)) {
            updates.title = suggestedTitle
            handleUpdateTitle(currentThreadId, suggestedTitle)
          }

          return { ...session, ...updates }
        }
        return session
      })
    )
  }

  // Send message
  const handleSend = async () => {
    if (!draft.trim() || isLoading || !isInitialized || !currentThreadId) return

    const currentSession = chatSessions.find((s) => s.thread_id === currentThreadId)
    const isFirstMessage = currentSession?.isFirstMessage || false

    const userMessage = {
      id: `m-${Date.now()}`,
      role: 'user',
      content: draft.trim(),
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }

    const newMessages = [...messages, userMessage]
    setMessages(newMessages)
    updateCurrentSessionMessages(newMessages)
    setDraft('')
    setIsLoading(true)

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage.content,
          thread_id: currentThreadId,
          is_first_message: isFirstMessage,
        }),
      })

      if (!response.ok) {
        throw new Error(
          `HTTP error! status: ${response.status}\nMessage: ${await response.text()}`
        )
      }

      const data = await response.json()

      // ✅ 新：容错提取 plan（解析成功/失败都能尽量显示 plan panel）
      console.log('🤖 AI 原始响应内容:', data.content)

      const { planData, displayContent, parseOk } = parsePlanFromModelContent(data.content)

      if (planData) {
        console.log(parseOk ? '✅ 提取到结构化 Plan JSON' : '🟡 解析失败，使用 Partial Plan')
        savePlan(currentThreadId, planData)
        setCurrentPlan(planData)
        setShowPlan(true)
      }

      const aiMessage = {
        id: `m-${Date.now()}-ai`,
        role: 'assistant',
        content: displayContent,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }

      const updatedMessages = [...newMessages, aiMessage]
      setMessages(updatedMessages)
      updateCurrentSessionMessages(updatedMessages, data.suggested_title)
    } catch (error) {
      console.error('Failed to send message:', error.message)
      const errorMessage = {
        id: `m-${Date.now()}-error`,
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }
      const updatedMessages = [...newMessages, errorMessage]
      setMessages(updatedMessages)
      updateCurrentSessionMessages(updatedMessages)
    } finally {
      setIsLoading(false)
    }
  }

  // Delete chat
  const handleDeleteChat = async (threadId) => {
    if (!confirm('Are you sure you want to delete this chat?')) return

    try {
      // Remove from list
      const updatedSessions = chatSessions.filter((s) => s.thread_id !== threadId)
      setChatSessions(updatedSessions)

      // If deleted chat is current, switch to first chat
      if (currentThreadId === threadId) {
        if (updatedSessions.length > 0) {
          const firstSession = updatedSessions[0]
          setCurrentThreadId(firstSession.thread_id)
          setMessages(firstSession.messages)
          localStorage.setItem('currentThreadId', firstSession.thread_id)
        } else {
          // If no chats left, create new chat
          handleNewChat()
        }
      }

      console.log('✅ Chat deleted:', threadId)
    } catch (error) {
      console.error('❌ Failed to delete chat:', error)
    }
  }

  // Pin/unpin chat
  const handlePinChat = (threadId) => {
    setChatSessions((prev) =>
      prev.map((session) =>
        session.thread_id === threadId
          ? { ...session, isPinned: !session.isPinned }
          : session
      )
    )
    console.log('Chat pin toggled:', threadId)
  }

  // Print current chat history
  const handleExport = () => {
    window.print()
  }

  // Sidebar drag ordering (display only).
  const handleReorderChats = (nextOrder) => {
    setChatOrder(nextOrder)
  }

  // Convert chat list format for Sidebar
  const chatHistoryItems = chatSessions.map((session) => ({
    id: session.id,
    thread_id: session.thread_id,
    title: session.title,
    preview: session.preview,
    isActive: session.thread_id === currentThreadId,
    isPinned: session.isPinned || false,
  }))

  // Filter chats by search query (title/preview/content)
  const filteredChatHistoryItems = (() => {
    const query = chatSearch.trim().toLowerCase()
    if (!query) return chatHistoryItems
    const sessionById = new Map(chatSessions.map((session) => [session.thread_id, session]))
    return chatHistoryItems.filter((item) => {
      const session = sessionById.get(item.thread_id)
      const content = session?.messages?.map((message) => message.content).join(' ') || ''
      const haystack = `${item.title} ${item.preview} ${content}`.toLowerCase()
      return haystack.includes(query)
    })
  })()

  const currentChatTitle =
    chatSessions.find((s) => s.thread_id === currentThreadId)?.title || 'Chat'

  return (
    <div className={`app-shell ${isSmallScreen && isSidebarOpen ? 'mobile-open' : ''}`}>
      <Sidebar
        items={filteredChatHistoryItems}
        order={chatOrder}
        onReorder={handleReorderChats}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        onUpdateTitle={handleUpdateTitle}
        onDeleteChat={handleDeleteChat}
        onPinChat={handlePinChat}
        onOpenDashboard={() => setActiveView('dashboard')}
        onOpenCalendar={() => setActiveView('calendar')}
        onOpenSettings={() => setActiveView('settings')}
        searchValue={chatSearch}
        onSearchChange={setChatSearch}
        isOpen={!isSmallScreen || isSidebarOpen}
        isSmallScreen={isSmallScreen}
        onToggleMenu={() => setIsSidebarOpen((prev) => !prev)}
      />

      <main className={`chat-panel ${activeView !== 'chat' ? 'panel-scroll' : ''}`}>
        {activeView === 'dashboard' ? (
          <Dashboard
            onBack={() => setActiveView('chat')}
            showMenuButton={isSmallScreen}
            onToggleMenu={() => setIsSidebarOpen((prev) => !prev)}
          />
        ) : activeView === 'calendar' ? (
          <Calendar
            onBack={() => setActiveView('chat')}
            showMenuButton={isSmallScreen}
            onToggleMenu={() => setIsSidebarOpen((prev) => !prev)}
          />
        ) : activeView === 'settings' ? (
          <Settings
            onBack={() => setActiveView('chat')}
            showMenuButton={isSmallScreen}
            onToggleMenu={() => setIsSidebarOpen((prev) => !prev)}
          />
        ) : (
          <div className="chat-container">
            <header className="chat-header">
              {isSmallScreen && (
                <button
                  className="menu-button"
                  type="button"
                  onClick={() => setIsSidebarOpen((prev) => !prev)}
                  aria-label="Toggle sidebar"
                >
                  <span className="menu-icon" aria-hidden="true" />
                </button>
              )}
              <div>
                {isEditingTitle ? (
                  <input
                    type="text"
                    className="chat-title-edit"
                    value={editTitleValue}
                    onChange={(e) => setEditTitleValue(e.target.value)}
                    onBlur={handleSaveTitleEdit}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleSaveTitleEdit()
                      if (e.key === 'Escape') handleCancelTitleEdit()
                    }}
                    autoFocus
                  />
                ) : (
                  <h1
                    onDoubleClick={handleStartEditTitle}
                    style={{ cursor: 'pointer' }}
                    title="Double-click to rename"
                  >
                    {currentChatTitle}
                  </h1>
                )}
                <p>Long term goals, broken into weekly steps.</p>
              </div>
              <div className="header-actions">
                <button className="ghost-button" onClick={handleExport}>
                  Export
                </button>
              </div>
            </header>

            <div className={`chat-content ${showPlan ? 'split-view' : ''}`}>
              <div className="chat-main">
                <section className="chat-scroll" ref={chatScrollRef}>
                  {messages.map((message) => (
                    <ChatMessage
                      key={message.id}
                      role={message.role}
                      content={message.content}
                      time={message.time}
                    />
                  ))}
                  {isLoading && (
                    <ChatMessage key="loading" role="assistant" content="Thinking..." time="" />
                  )}
                </section>

                <ChatInput value={draft} onChange={setDraft} onSend={handleSend} />
              </div>

              {showPlan && (
                <div className="plan-panel">
                  <TentativePlan plan={currentPlan} threadId={currentThreadId} />
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
