import { useEffect, useState } from 'react'
import ChatInput from './components/ChatInput'
import ChatMessage from './components/ChatMessage'
import Dashboard from './components/Dashboard'
import Sidebar from './components/Sidebar'
import './App.css'

const API_BASE_URL = 'http://localhost:8000'

// Temporary mock data until we wire the backend.
const chatHistory = [
  { id: 'plan', title: 'My Life Plan', preview: 'Break down goals for Q1...' },
  { id: 'visa', title: 'Visa Checklist', preview: 'Collect bank statements...' },
  { id: 'french', title: 'Learn French', preview: 'Practice 20 min daily...' },
  { id: 'fitness', title: 'Fitness Sprint', preview: '3 workouts this week' },
]

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
  const [messages, setMessages] = useState(initialMessages)
  const [draft, setDraft] = useState('')
  const [activeView, setActiveView] = useState('chat')
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [isSmallScreen, setIsSmallScreen] = useState(false)
  const [threadId, setThreadId] = useState(null)
  const [assistantId, setAssistantId] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isInitialized, setIsInitialized] = useState(false)

  // 用户登录时初始化
  useEffect(() => {
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
        setThreadId(data.thread_id)
        setAssistantId(data.assistant_id)
        setIsInitialized(true)
        
        console.log('✅ Chat initialized:', data.message)
      } catch (error) {
        console.error('❌ Initialization failed:', error)
      }
    }

    initializeChat()
  }, [])

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

  // Send message to backend and get AI response
  const handleSend = async () => {
    if (!draft.trim() || isLoading || !isInitialized) return
    
    const userMessage = {
      id: `m-${Date.now()}`,
      role: 'user',
      content: draft.trim(),
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }
    
    setMessages((prev) => [...prev, userMessage])
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
          thread_id: threadId,
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()

      // Add AI response to messages
      const aiMessage = {
        id: `m-${Date.now()}-ai`,
        role: 'assistant',
        content: data.content,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }
      
      setMessages((prev) => [...prev, aiMessage])
    } catch (error) {
      console.error('Failed to send message:', error)
      // Show error message in chat
      const errorMessage = {
        id: `m-${Date.now()}-error`,
        role: 'assistant',
        content: '❌ Sorry, I encountered an error. Please try again.',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className={`app-shell ${isSmallScreen && isSidebarOpen ? 'mobile-open' : ''}`}>
      {/* Left column stays fixed to show chat history */}
      <Sidebar
        items={chatHistory}
        onOpenDashboard={() => setActiveView('dashboard')}
        isOpen={!isSmallScreen || isSidebarOpen}
        isSmallScreen={isSmallScreen}
        onToggleMenu={() => setIsSidebarOpen((prev) => !prev)}
      />

      {/* Right column holds the conversation and input */}
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
                <h1>My Life Plan</h1>
                <p>Long term goals, broken into weekly steps.</p>
              </div>
              <button className="ghost-button">Export</button>
            </header>

            {/* Scrollable message list */}
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

            {/* Input stays visible at the bottom */}
            <ChatInput value={draft} onChange={setDraft} onSend={handleSend} />
          </>
        )}
      </main>
    </div>
  )
}

export default App
