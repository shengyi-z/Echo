import { useEffect, useState } from 'react'
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

  // 用户登录时初始化或加载保存的对话
  useEffect(() => {
    const savedSessions = localStorage.getItem('chatSessions')
    const savedThreadId = localStorage.getItem('currentThreadId')
    const savedAssistantId = localStorage.getItem('assistantId')
    
    // 如果有保存的数据，直接加载
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

    // 否则初始化新对话
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
          title: 'My Life Plan',
          preview: 'Break down goals...',
          messages: [...initialMessages]
        }
        setChatSessions([newSession])
        
        // 立即保存到 localStorage
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

  // 保存对话历史到 localStorage（当会话更新时）
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

  // 创建新对话
  const handleNewChat = async () => {
    try {
      console.log('🆕 Creating new chat...')
      const response = await fetch(`${API_BASE_URL}/api/chat/new`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: `Chat ${chatSessions.length + 1}`
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
        title: data.title,
        preview: 'Start a new conversation...',
        messages: [...initialMessages]
      }
      
      setChatSessions(prev => [...prev, newSession])
      setCurrentThreadId(data.thread_id)
      setMessages([...initialMessages])
      setActiveView('chat')
      
      // 立即保存
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

  // 更新当前对话的消息
  const updateCurrentSessionMessages = (newMessages) => {
    setChatSessions(prev => 
      prev.map(session => 
        session.thread_id === currentThreadId
          ? { 
              ...session, 
              messages: newMessages, 
              preview: newMessages[newMessages.length - 1]?.content?.slice(0, 30) + '...' || 'No messages'
            }
          : session
      )
    )
  }

  // 发送消息
  const handleSend = async () => {
    if (!draft.trim() || isLoading || !isInitialized || !currentThreadId) return
    
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
      updateCurrentSessionMessages(updatedMessages)
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

  // 转换对话列表格式给 Sidebar
  const chatHistoryItems = chatSessions.map(session => ({
    id: session.id,
    title: session.title,
    preview: session.preview
  }))

  return (
    <div className={`app-shell ${isSmallScreen && isSidebarOpen ? 'mobile-open' : ''}`}>
      <Sidebar
        items={chatHistoryItems}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
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
                <h1>{chatSessions.find(s => s.thread_id === currentThreadId)?.title || 'Chat'}</h1>
                <p>Long term goals, broken into weekly steps.</p>
              </div>
              <button className="ghost-button">Export</button>
            </header>

            <section className="chat-scroll">
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
