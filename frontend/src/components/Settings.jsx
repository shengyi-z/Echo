// 设置页：静态开关占位，后续可接入后端。
function Settings({ onBack, showMenuButton, onToggleMenu }) {
  return (
    <div className="settings">
      {/* 设置头部 */}
      <header className="settings-header">
        <div className="settings-actions">
          {showMenuButton && (
            <button
              className="menu-button"
              type="button"
              onClick={onToggleMenu}
              aria-label="Toggle sidebar"
            >
              <span className="menu-icon" aria-hidden="true" />
            </button>
          )}
        </div>
        <div>
          <h1>Settings</h1>
          <p>Personalize reminders, privacy, and display.</p>
        </div>
      </header>

      {/* 设置卡片网格 */}
      <section className="settings-grid">
        <article className="dash-card">
          <header className="dash-card-header">
            <h2>Reminders</h2>
            <span className="pill ghost">On/Off</span>
          </header>
          <label className="settings-toggle">
            <input type="checkbox" defaultChecked />
            <span>Daily reminder</span>
          </label>
          <label className="settings-toggle">
            <input type="checkbox" />
            <span>Weekly summary</span>
          </label>
        </article>

        <article className="dash-card">
          <header className="dash-card-header">
            <h2>Privacy</h2>
            <span className="pill ghost">Controls</span>
          </header>
          <label className="settings-toggle">
            <input type="checkbox" defaultChecked />
            <span>Hide sensitive previews</span>
          </label>
          <label className="settings-toggle">
            <input type="checkbox" />
            <span>Mask timestamps in sidebar</span>
          </label>
        </article>

        <article className="dash-card">
          <header className="dash-card-header">
            <h2>Display</h2>
            <span className="pill ghost">Layout</span>
          </header>
          <label className="settings-toggle">
            <input type="checkbox" defaultChecked />
            <span>Compact chat bubbles</span>
          </label>
          <label className="settings-toggle">
            <input type="checkbox" />
            <span>Show timestamps</span>
          </label>
        </article>
      </section>

      {/* 底部操作区 */}
      <div className="settings-footer">
        <button className="back-button" type="button" onClick={onBack}>
          Back
        </button>
      </div>
    </div>
  )
}

export default Settings
