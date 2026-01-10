import { useEffect, useRef } from 'react'

const MAX_INPUT_HEIGHT = 160

// Input bar anchored at the bottom of the chat panel.
function ChatInput({ value, onChange, onSend }) {
  const textareaRef = useRef(null)

  // Resize the textarea to fit content, up to a capped height.
  useEffect(() => {
    const textarea = textareaRef.current
    if (!textarea) return
    textarea.style.height = 'auto'
    textarea.style.height = `${Math.min(textarea.scrollHeight, MAX_INPUT_HEIGHT)}px`
  }, [value])

  return (
    <form
      className="chat-input"
      onSubmit={(event) => {
        event.preventDefault()
        onSend()
      }}
    >
      <label className="sr-only" htmlFor="chat-message">
        Type your message
      </label>
      <textarea
        id="chat-message"
        ref={textareaRef}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="Ask Echo to plan your next step..."
        rows={1}
      />
      <button type="submit" className="send-button">
        Send
      </button>
    </form>
  )
}

export default ChatInput
