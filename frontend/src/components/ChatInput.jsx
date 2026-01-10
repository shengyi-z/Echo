// Input bar anchored at the bottom of the chat panel.
function ChatInput({ value, onChange, onSend }) {
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
