import ChatHistoryItem from './ChatHistoryItem'

// Left rail with chat history and navigation.
function Sidebar({ items, onSelectChat, onNewChat, onUpdateTitle, onDeleteChat, onPinChat, onOpenDashboard, isOpen, isSmallScreen, onToggleMenu }) {
  // 按 isPinned 排序：置顶的在前
  const sortedItems = [...items].sort((a, b) => {
    if (a.isPinned && !b.isPinned) return -1
    if (!a.isPinned && b.isPinned) return 1
    return 0
  })

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
        {sortedItems.map((item) => (
          <ChatHistoryItem
            key={item.id}
            title={item.title}
            preview={item.preview}
            isActive={item.isActive}
            isPinned={item.isPinned}
            onClick={() => onSelectChat(item.id)}
            onRename={(newTitle) => onUpdateTitle(item.thread_id, newTitle)}
            onDelete={() => onDeleteChat(item.thread_id)}
            onPin={() => onPinChat(item.thread_id)}
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
