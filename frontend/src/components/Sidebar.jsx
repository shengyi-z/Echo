import ChatHistoryItem from './ChatHistoryItem'

// Left rail with chat history and navigation.
function Sidebar({ items, onSelectChat, onNewChat, onOpenDashboard, isOpen, isSmallScreen, onToggleMenu, currentThreadId }) {
  return (
    <aside className={`sidebar ${isOpen ? 'open' : ''} ${isSmallScreen ? 'mobile' : ''}`}>
      <div className="sidebar-header">
        {isSmallScreen ? (
          <button className="logo-button" type="button" onClick={onToggleMenu}>
            <span className="logo-mark">Echo</span>
          </button>
        ) : (
          <div className="logo-mark">Echo</div>
        )}
        <button className="new-chat" onClick={onNewChat}>New Chat</button>
      </div>
      <div className="history-list">
        {items.map((item) => (
          <ChatHistoryItem
            key={item.id}
            title={item.title}
            preview={item.preview}
            isActive={item.isActive}
            onClick={() => onSelectChat(item.id)}
          />
        ))}
      </div>
      <div className="sidebar-footer">
        <button className="nav-tab" type="button" onClick={onOpenDashboard}>
          Dashboard
        </button>
        <div className="profile-chip">Karen</div>
      </div>
    </aside>
  )
}

export default Sidebar
