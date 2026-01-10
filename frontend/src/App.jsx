import { useEffect, useState, useRef } from 'react'
import ChatInput from './components/ChatInput'
import ChatMessage from './components/ChatMessage'
import Dashboard from './components/Dashboard'
import Sidebar from './components/Sidebar'
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
  const chatScrollRef = useRef(null)

  // 自动滚动到最新消息
  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight
    }
  }, [messages])

  // 用户登录时初始化或加载保存的对话
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
      
      const currentSession = sessions.find(s => s.thread_id === savedThreadId)
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
          isFirstMessage: true
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

  // 保存对话历史到 localStorage
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

  // 生成唯一的 New Chat 标题
  const getUniqueNewChatTitle = () => {
    const existingTitles = chatSessions.map(s => s.title)
    let counter = 1
    let title = 'New Chat'
    
    // 如果 "New Chat" 已存在，尝试 "New Chat 1", "New Chat 2"...
    while (existingTitles.includes(title)) {
      title = `New Chat ${counter}`
      counter++
    }
    
    return title
  }

  // 创建新对话
  const handleNewChat = async () => {
    try {
      console.log('🆕 Creating new chat...')
      console.log('Current sessions:', chatSessions.map(s => s.title))
      
      const uniqueTitle = getUniqueNewChatTitle()
      console.log('Generated unique title:', uniqueTitle)
      
      const response = await fetch(`${API_BASE_URL}/api/chat/new`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: uniqueTitle
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
        isFirstMessage: true
      }
      
      setChatSessions(prev => {
        const updated = [...prev, newSession]
        console.log('Updated sessions:', updated.map(s => s.title))
        return updated
      })
      setCurrentThreadId(data.thread_id)
      setMessages([...initialMessages])
      setActiveView('chat')
      
      localStorage.setItem('currentThreadId', data.thread_id)
      
      console.log('📝 Chat sessions updated')
    } catch (error) {
      console.error('❌ Failed to create new chat:', error)
    }
  }

  // 切换对话
  const handleSelectChat = (chatId) => {
    const session = chatSessions.find(s => s.id === chatId)
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

  // 更新对话标题
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
          title: newTitle.trim()
        }),
      })

      setChatSessions(prev =>
        prev.map(session =>
          session.thread_id === threadId
            ? { ...session, title: newTitle.trim() }
            : session
        )
      )
      
      console.log('✅ Title updated:', newTitle)
    } catch (error) {
      console.error('❌ Failed to update title:', error)
    }
  }

  // 开始编辑标题（Chat Area）
  const handleStartEditTitle = () => {
    const currentSession = chatSessions.find(s => s.thread_id === currentThreadId)
    if (currentSession) {
      setEditTitleValue(currentSession.title)
      setIsEditingTitle(true)
    }
  }

  // 保存标题编辑（Chat Area）
  const handleSaveTitleEdit = () => {
    if (editTitleValue.trim() && currentThreadId) {
      handleUpdateTitle(currentThreadId, editTitleValue.trim())
    }
    setIsEditingTitle(false)
  }

  // 取消标题编辑（Chat Area）
  const handleCancelTitleEdit = () => {
    setIsEditingTitle(false)
    setEditTitleValue('')
  }

  // 更新当前对话的消息
  const updateCurrentSessionMessages = (newMessages, suggestedTitle = null) => {
    setChatSessions(prev =>
      prev.map(session => {
        if (session.thread_id === currentThreadId) {
          const updates = {
            messages: newMessages,
            preview: newMessages[newMessages.length - 1]?.content?.slice(0, 30) + '...' || 'No messages',
            isFirstMessage: false
          }
          
          // 如果有建议的标题，并且当前标题还是 "New Chat" 系列，则自动更新
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

  // 发送消息
  const handleSend = async () => {
    if (!draft.trim() || isLoading || !isInitialized || !currentThreadId) return
    
    const currentSession = chatSessions.find(s => s.thread_id === currentThreadId)
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
          is_first_message: isFirstMessage
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()

      const aiMessage = {
        id: `m-${Date.now()}-ai`,
        role: 'assistant',
        content: data.content,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }
      
      const updatedMessages = [...newMessages, aiMessage]
      setMessages(updatedMessages)
      updateCurrentSessionMessages(updatedMessages, data.suggested_title)
    } catch (error) {
      console.error('Failed to send message:', error)
      const errorMessage = {
        id: `m-${Date.now()}-error`,
        role: 'assistant',
        content: '❌ Sorry, I encountered an error. Please try again.',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }
      const updatedMessages = [...newMessages, errorMessage]
      setMessages(updatedMessages)
      updateCurrentSessionMessages(updatedMessages)
    } finally {
      setIsLoading(false)
    }
  }

  // 删除对话
  const handleDeleteChat = async (threadId) => {
    if (!confirm('Are you sure you want to delete this chat?')) return
    
    try {
      // 从列表中移除
      const updatedSessions = chatSessions.filter(s => s.thread_id !== threadId)
      setChatSessions(updatedSessions)
      
      // 如果删除的是当前对话，切换到第一个对话
      if (currentThreadId === threadId) {
        if (updatedSessions.length > 0) {
          const firstSession = updatedSessions[0]
          setCurrentThreadId(firstSession.thread_id)
          setMessages(firstSession.messages)
          localStorage.setItem('currentThreadId', firstSession.thread_id)
        } else {
          // 如果没有对话了，创建新对话
          handleNewChat()
        }
      }
      
      console.log('✅ Chat deleted:', threadId)
    } catch (error) {
      console.error('❌ Failed to delete chat:', error)
    }
  }

  // 置顶/取消置顶对话
  const handlePinChat = (threadId) => {
    setChatSessions(prev =>
      prev.map(session =>
        session.thread_id === threadId
          ? { ...session, isPinned: !session.isPinned }
          : session
      )
    )
    console.log('✅ Chat pin toggled:', threadId)
  }

  // 转换对话列表格式给 Sidebar
  const chatHistoryItems = chatSessions.map(session => ({
    id: session.id,
    thread_id: session.thread_id,
    title: session.title,
    preview: session.preview,
    isActive: session.thread_id === currentThreadId,
    isPinned: session.isPinned || false
  }))

  const currentChatTitle = chatSessions.find(s => s.thread_id === currentThreadId)?.title || 'Chat'

  return (
    <div className={`app-shell ${isSmallScreen && isSidebarOpen ? 'mobile-open' : ''}`}>
      <Sidebar
        items={chatHistoryItems}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        onUpdateTitle={handleUpdateTitle}
        onDeleteChat={handleDeleteChat}
        onPinChat={handlePinChat}
        onOpenDashboard={() => setActiveView('dashboard')}
        isOpen={!isSmallScreen || isSidebarOpen}
        isSmallScreen={isSmallScreen}
        onToggleMenu={() => setIsSidebarOpen((prev) => !prev)}
      />

      <main className="chat-panel">
        {activeView === 'dashboard' ? (
          <Dashboard
            onBack={() => setActiveView('chat')}
            showMenuButton={isSmallScreen}
            onToggleMenu={() => setIsSidebarOpen((prev) => !prev)}
          />
        ) : (
          <>
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
              <button className="ghost-button">Export</button>
            </header>

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
                <ChatMessage
                  key="loading"
                  role="assistant"
                  content="Thinking..."
                  time=""
                />
              )}
            </section>

            <ChatInput value={draft} onChange={setDraft} onSend={handleSend} />
          </>
        )}
      </main>
    </div>
  )
}

export default App
