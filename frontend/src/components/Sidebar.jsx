import { useState } from 'react'
import ChatHistoryItem from './ChatHistoryItem'

// Left rail with chat history and navigation.
function Sidebar({
  items,
  order,
  onReorder,
  onSelectChat,
  onNewChat,
  onUpdateTitle,
  onDeleteChat,
  onPinChat,
  onOpenCalendar,
  onOpenDashboard,
  onOpenSettings,
  searchValue,
  onSearchChange,
  isOpen,
  isSmallScreen,
  onToggleMenu,
}) {
  // 拖拽状态
  const [draggingId, setDraggingId] = useState(null)
  const [dragOverId, setDragOverId] = useState(null)

  // 构建稳定的显示顺序（置顶仍在前）。
  const itemById = new Map(items.map((item) => [item.thread_id, item]))
  const orderedIds = (order && order.length > 0 ? order : items.map((item) => item.thread_id))
    .filter((id) => itemById.has(id))
  const missingIds = items
    .map((item) => item.thread_id)
    .filter((id) => !orderedIds.includes(id))
  const orderedItems = [...orderedIds, ...missingIds].map((id) => itemById.get(id))
  const pinnedItems = orderedItems.filter((item) => item.isPinned)
  const unpinnedItems = orderedItems.filter((item) => !item.isPinned)
  const sortedItems = [...pinnedItems, ...unpinnedItems]

  // 移动排序数组中的条目。
  const moveItem = (list, sourceId, targetId, placeAfter = false) => {
    if (!sourceId || !targetId || sourceId === targetId) return list
    const next = list.filter((id) => id !== sourceId)
    const targetIndex = next.indexOf(targetId)
    if (targetIndex === -1) return list
    const insertAt = placeAfter ? targetIndex + 1 : targetIndex
    next.splice(insertAt, 0, sourceId)
    return next
  }

  // 拖拽开始
  const handleDragStart = (id) => (event) => {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', id)
    setDraggingId(id)
  }

  // 拖拽经过
  const handleDragOver = (id) => (event) => {
    event.preventDefault()
    setDragOverId(id)
  }

  // 拖拽释放到目标
  const handleDrop = (targetId) => (event) => {
    event.preventDefault()
    event.stopPropagation()
    const sourceId = draggingId || event.dataTransfer.getData('text/plain')
    setDragOverId(null)
    setDraggingId(null)
    if (!sourceId || sourceId === targetId) return

    const sourceItem = itemById.get(sourceId)
    const targetItem = itemById.get(targetId)
    if (!sourceItem || !targetItem) return
    if (sourceItem.isPinned !== targetItem.isPinned) return

    const nextOrder = moveItem([...orderedIds, ...missingIds], sourceId, targetId)
    onReorder(nextOrder)
  }

  // 拖拽释放到列表底部
  const handleDropOnList = (event) => {
    event.preventDefault()
    const sourceId = draggingId || event.dataTransfer.getData('text/plain')
    setDragOverId(null)
    setDraggingId(null)
    if (!sourceId) return

    const sourceItem = itemById.get(sourceId)
    if (!sourceItem) return
    const group = sortedItems.filter((item) => item.isPinned === sourceItem.isPinned)
    const lastId = group[group.length - 1]?.thread_id
    if (!lastId || lastId === sourceId) return

    const nextOrder = moveItem([...orderedIds, ...missingIds], sourceId, lastId, true)
    onReorder(nextOrder)
  }

  // 拖拽结束
  const handleDragEnd = () => {
    setDragOverId(null)
    setDraggingId(null)
  }

  return (
    <aside className={`sidebar ${isOpen ? 'open' : ''} ${isSmallScreen ? 'mobile' : ''}`}>
      {/* 侧边栏头部 */}
      <div className="sidebar-header">
        {isSmallScreen ? (
          <button className="logo-button" type="button" onClick={onToggleMenu}>
            <span className="logo-mark">Echo</span>
          </button>
        ) : (
          <div className="logo-mark">Echo</div>
        )}
        <button className="new-chat" onClick={onNewChat}>New Chat</button>
        {/* 搜索对话 */}
        <div className="chat-search">
          <input
            type="text"
            value={searchValue}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="Search chats"
            aria-label="Search chats"
          />
        </div>
      </div>
      {/* 对话列表 */}
      <div className="history-list" onDragOver={(event) => event.preventDefault()} onDrop={handleDropOnList}>
        {sortedItems.map((item) => (
          <ChatHistoryItem
            key={item.id}
            title={item.title}
            preview={item.preview}
            isActive={item.isActive}
            isPinned={item.isPinned}
            isDragging={draggingId === item.thread_id}
            isDragOver={dragOverId === item.thread_id}
            onClick={() => onSelectChat(item.id)}
            onRename={(newTitle) => onUpdateTitle(item.thread_id, newTitle)}
            onDelete={() => onDeleteChat(item.thread_id)}
            onPin={() => onPinChat(item.thread_id)}
            onDragStart={handleDragStart(item.thread_id)}
            onDragOver={handleDragOver(item.thread_id)}
            onDrop={handleDrop(item.thread_id)}
            onDragEnd={handleDragEnd}
          />
        ))}
      </div>
      {/* 侧边栏底部 */}
      <div className="sidebar-footer">
        <button className="nav-tab" type="button" onClick={onOpenCalendar}>
          Calendar
        </button>
        <button className="nav-tab" type="button" onClick={onOpenDashboard}>
          Dashboard
        </button>
        <div className="sidebar-profile">
          <div className="profile-chip">Karen</div>
          <button className="settings-button" type="button" onClick={onOpenSettings}>
            Settings
          </button>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar
