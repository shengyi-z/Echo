import ChatHistoryItem from './ChatHistoryItem'

// Left rail with chat history and navigation.
function Sidebar({ items, onOpenDashboard, isOpen, isSmallScreen, onToggleMenu }) {
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
        <button className="nav-tab" type="button" onClick={onOpenDashboard}>
          Dashboard
        </button>
        <div className="profile-chip">Karen</div>
      </div>
    </aside>
  )
}

export default Sidebar
