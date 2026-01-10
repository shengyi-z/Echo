// Single item in the chat history list.
function ChatHistoryItem({ title, preview, isActive, onClick }) {
  return (
    <button 
      className={`history-item ${isActive ? 'active' : ''}`}
      onClick={onClick}
    >
      <div className="history-title">{title}</div>
      <div className="history-preview">{preview}</div>
    </button>
  )
}

export default ChatHistoryItem
