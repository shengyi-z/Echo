import ChatHistoryItem from './ChatHistoryItem'

// Left rail with chat history and actions.
function Sidebar({ items }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="logo-mark">Echo</div>
        <button className="new-chat">New Chat</button>
      </div>
      <div className="history-list">
        {items.map((item, index) => (
          <ChatHistoryItem
            key={item.id}
            title={item.title}
            preview={item.preview}
            isActive={index === 0}
          />
        ))}
      </div>
      <div className="sidebar-footer">
        <div className="profile-chip">Karen</div>
      </div>
    </aside>
  )
}

export default Sidebar
