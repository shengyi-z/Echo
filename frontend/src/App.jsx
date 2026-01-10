import { useState } from 'react'
import ChatInput from './components/ChatInput'
import ChatMessage from './components/ChatMessage'
import Dashboard from './components/Dashboard'
import Sidebar from './components/Sidebar'
import './App.css'

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
  {
    id: 'm2',
    role: 'user',
    content: 'I want to get my driver license before August.',
    time: '09:12',
  },
  {
    id: 'm3',
    role: 'assistant',
    content:
      'Great. We will split it into milestones: theory, materials, booking, and test. Which city are you in?',
    time: '09:13',
  },
]

function App() {
  const [messages, setMessages] = useState(initialMessages)
  const [draft, setDraft] = useState('')
  const [activeView, setActiveView] = useState('chat')

  // Push the current draft into the message list.
  const handleSend = () => {
    if (!draft.trim()) return
    const next = {
      id: `m-${Date.now()}`,
      role: 'user',
      content: draft.trim(),
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }
    setMessages((prev) => [...prev, next])
    setDraft('')
  }

  return (
    <div className="app-shell">
      {/* Left column stays fixed to show chat history */}
      <Sidebar items={chatHistory} onOpenDashboard={() => setActiveView('dashboard')} />

      {/* Right column holds the conversation and input */}
      <main className="chat-panel">
        {activeView === 'dashboard' ? (
          <Dashboard onBack={() => setActiveView('chat')} />
        ) : (
          <>
            <header className="chat-header">
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
