import { useState, useRef, useEffect } from 'react'

// Single item in the chat history list.
function ChatHistoryItem({ title, preview, isActive, isPinned, onClick, onRename, onDelete, onPin }) {
  const [isEditing, setIsEditing] = useState(false)
  const [editTitle, setEditTitle] = useState(title)
  const [showMenu, setShowMenu] = useState(false)
  const [menuStyle, setMenuStyle] = useState(null)
  const menuRef = useRef(null)
  const menuContainerRef = useRef(null)

  // 点击外部关闭菜单
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuContainerRef.current && !menuContainerRef.current.contains(event.target)) {
        setShowMenu(false)
      }
    }

    if (showMenu) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showMenu])

  // Position the menu so it doesn't get clipped by the scroll container.
  useEffect(() => {
    if (!showMenu) {
      setMenuStyle(null)
      return
    }

    const menu = menuRef.current
    const anchor = menuContainerRef.current
    if (!menu || !anchor) return

    const padding = 8
    const gap = 4

    const updatePosition = () => {
      const anchorRect = anchor.getBoundingClientRect()
      const menuRect = menu.getBoundingClientRect()
      const fitsBelow = anchorRect.bottom + menuRect.height + gap <= window.innerHeight - padding
      const top = fitsBelow
        ? anchorRect.bottom + gap
        : anchorRect.top - menuRect.height - gap
      const left = Math.min(
        window.innerWidth - menuRect.width - padding,
        Math.max(padding, anchorRect.right - menuRect.width)
      )

      setMenuStyle({
        top: `${Math.max(padding, top)}px`,
        left: `${left}px`
      })
    }

    updatePosition()
    window.addEventListener('resize', updatePosition)
    return () => window.removeEventListener('resize', updatePosition)
  }, [showMenu])

  const handleDoubleClick = (e) => {
    e.stopPropagation()
    setEditTitle(title)
    setIsEditing(true)
  }

  const handleSave = () => {
    if (editTitle.trim() && editTitle !== title) {
      onRename(editTitle.trim())
    } else {
      setEditTitle(title)
    }
    setIsEditing(false)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleSave()
    } else if (e.key === 'Escape') {
      setEditTitle(title)
      setIsEditing(false)
    }
  }

  const handleBlur = () => {
    handleSave()
  }

  const handleMenuClick = (e) => {
    e.stopPropagation()
    setShowMenu((prev) => !prev)
  }

  const handleDelete = (e) => {
    e.stopPropagation()
    setShowMenu(false)
    onDelete()
  }

  const handlePin = (e) => {
    e.stopPropagation()
    setShowMenu(false)
    onPin()
  }

  return (
    <div className={`history-item-wrapper ${isActive ? 'active' : ''}`}>
      <button 
        className={`history-item ${isActive ? 'active' : ''} ${isPinned ? 'pinned' : ''}`}
        onClick={!isEditing ? onClick : undefined}
        onDoubleClick={handleDoubleClick}
        title="Double-click to rename"
      >
        {isPinned && <span className="pin-icon">📌</span>}
        {isEditing ? (
          <div className="history-content">
            <input
              type="text"
              className="history-title-edit"
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              onBlur={handleBlur}
              onKeyDown={handleKeyDown}
              onClick={(e) => e.stopPropagation()}
              autoFocus
            />
          </div>
        ) : (
          <div className="history-content">
            <div className="history-title">{title}</div>
            <div className="history-preview">{preview}</div>
          </div>
        )}
      </button>

      <div ref={menuContainerRef}>
      <button 
        className="history-menu-button"
        onClick={handleMenuClick}
        title="More options"
      >
        ⋮
      </button>

        {showMenu && (
          <div
            className="history-menu"
            ref={menuRef}
            style={menuStyle ? { ...menuStyle, visibility: 'visible' } : { visibility: 'hidden' }}
          >
          <button className="history-menu-item" onClick={handlePin}>
            {isPinned ? '📌 Unpin Chat' : '📌 Pin Chat'}
          </button>
          <button className="history-menu-item delete" onClick={handleDelete}>
            🗑️ Delete Chat
          </button>
        </div>
      )}
      </div>
    </div>
  )
}

export default ChatHistoryItem
