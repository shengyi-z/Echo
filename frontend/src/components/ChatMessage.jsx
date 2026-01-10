// Bubble for one message in the conversation.
function ChatMessage({ role, content, time }) {
  return (
    <div className={`chat-message ${role}`}>
      <div className="message-bubble">
        <p>{content}</p>
        <span className="message-time">{time}</span>
      </div>
    </div>
  )
}

export default ChatMessage
