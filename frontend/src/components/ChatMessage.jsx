// Bubble for one message in the conversation.
import ReactMarkdown from 'react-markdown'

function ChatMessage({ role, content, time }) {
  return (
    <div className={`chat-message ${role}`}>
      <div className="message-bubble">
        <div className="message-content">
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
        <span className="message-time">{time}</span>
      </div>
    </div>
  )
}

export default ChatMessage
