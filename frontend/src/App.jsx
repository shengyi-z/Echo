import { useEffect, useState, useRef } from 'react'
import ChatInput from './components/ChatInput'
import ChatMessage from './components/ChatMessage'
import Calendar from './components/Calendar'
import Dashboard from './components/Dashboard'
import Settings from './components/Settings'
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
  const [chatOrder, setChatOrder] = useState([])
  const [chatSearch, setChatSearch] = useState('')
  const chatScrollRef = useRef(null)

  // 鑷姩婊氬姩鍒版渶鏂版秷鎭?
  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight
    }
  }, [messages])

  // 鐢ㄦ埛鐧诲綍鏃跺垵濮嬪寲鎴栧姞杞戒繚瀛樼殑瀵硅瘽
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
      
      console.log('鉁?Loaded saved sessions from localStorage')
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
        
        console.log('鉁?Chat initialized:', data.message)
      } catch (error) {
        console.error('鉂?Initialization failed:', error)
      }
    }

    initializeChat()
  }, [])

  // 淇濆瓨瀵硅瘽鍘嗗彶鍒?localStorage
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

  // 鐢熸垚鍞竴鐨?New Chat 鏍囬
  const getUniqueNewChatTitle = () => {
    const existingTitles = chatSessions.map(s => s.title)
    let counter = 1
    let title = 'New Chat'
    
    // 濡傛灉 "New Chat" 宸插瓨鍦紝灏濊瘯 "New Chat 1", "New Chat 2"...
    while (existingTitles.includes(title)) {
      title = `New Chat ${counter}`
      counter++
    }
    
    return title
  }

  // 鍒涘缓鏂板璇?
  const handleNewChat = async () => {
    try {
      console.log('馃啎 Creating new chat...')
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
      console.log('鉁?New chat created:', data)
      
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
      
      console.log('馃摑 Chat sessions updated')
    } catch (error) {
      console.error('鉂?Failed to create new chat:', error)
    }
  }

  // 鍒囨崲瀵硅瘽
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

  // 鏇存柊瀵硅瘽鏍囬
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
      
      console.log('鉁?Title updated:', newTitle)
    } catch (error) {
      console.error('鉂?Failed to update title:', error)
    }
  }

  // 寮€濮嬬紪杈戞爣棰橈紙Chat Area锛?
  const handleStartEditTitle = () => {
    const currentSession = chatSessions.find(s => s.thread_id === currentThreadId)
    if (currentSession) {
      setEditTitleValue(currentSession.title)
      setIsEditingTitle(true)
    }
  }

  // 淇濆瓨鏍囬缂栬緫锛圕hat Area锛?
  const handleSaveTitleEdit = () => {
    if (editTitleValue.trim() && currentThreadId) {
      handleUpdateTitle(currentThreadId, editTitleValue.trim())
    }
    setIsEditingTitle(false)
  }

  // 鍙栨秷鏍囬缂栬緫锛圕hat Area锛?
  const handleCancelTitleEdit = () => {
    setIsEditingTitle(false)
    setEditTitleValue('')
  }

  // 鏇存柊褰撳墠瀵硅瘽鐨勬秷鎭?
  const updateCurrentSessionMessages = (newMessages, suggestedTitle = null) => {
    setChatSessions(prev =>
      prev.map(session => {
        if (session.thread_id === currentThreadId) {
          const updates = {
            messages: newMessages,
            preview: newMessages[newMessages.length - 1]?.content?.slice(0, 30) + '...' || 'No messages',
            isFirstMessage: false
          }
          
          // 濡傛灉鏈夊缓璁殑鏍囬锛屽苟涓斿綋鍓嶆爣棰樿繕鏄?"New Chat" 绯诲垪锛屽垯鑷姩鏇存柊
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

  // 鍙戦€佹秷鎭?
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

  // 鍒犻櫎瀵硅瘽
  const handleDeleteChat = async (threadId) => {
    if (!confirm('Are you sure you want to delete this chat?')) return
    
    try {
      // 浠庡垪琛ㄤ腑绉婚櫎
      const updatedSessions = chatSessions.filter(s => s.thread_id !== threadId)
      setChatSessions(updatedSessions)
      
      // 濡傛灉鍒犻櫎鐨勬槸褰撳墠瀵硅瘽锛屽垏鎹㈠埌绗竴涓璇?
      if (currentThreadId === threadId) {
        if (updatedSessions.length > 0) {
          const firstSession = updatedSessions[0]
          setCurrentThreadId(firstSession.thread_id)
          setMessages(firstSession.messages)
          localStorage.setItem('currentThreadId', firstSession.thread_id)
        } else {
          // 濡傛灉娌℃湁瀵硅瘽浜嗭紝鍒涘缓鏂板璇?
          handleNewChat()
        }
      }
      
      console.log('鉁?Chat deleted:', threadId)
    } catch (error) {
      console.error('鉂?Failed to delete chat:', error)
    }
  }

  // 缃《/鍙栨秷缃《瀵硅瘽
  const handlePinChat = (threadId) => {
    setChatSessions(prev =>
      prev.map(session =>
        session.thread_id === threadId
          ? { ...session, isPinned: !session.isPinned }
          : session
      )
    )
    console.log('Chat pin toggled:', threadId)
  }

  // 打印当前对话记录。
  const handleExport = () => {
    window.print()
  }

  // Sidebar drag ordering (display only).
  const handleReorderChats = (nextOrder) => {
    setChatOrder(nextOrder)
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

  // 根据搜索词过滤对话（标题/预览/内容）。
  const filteredChatHistoryItems = (() => {
    const query = chatSearch.trim().toLowerCase()
    if (!query) return chatHistoryItems
    const sessionById = new Map(chatSessions.map(session => [session.thread_id, session]))
    return chatHistoryItems.filter(item => {
      const session = sessionById.get(item.thread_id)
      const content = session?.messages?.map(message => message.content).join(' ') || ''
      const haystack = `${item.title} ${item.preview} ${content}`.toLowerCase()
      return haystack.includes(query)
    })
  })()

  const currentChatTitle = chatSessions.find(s => s.thread_id === currentThreadId)?.title || 'Chat'

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
              <button className="ghost-button" onClick={handleExport}>Export</button>
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








