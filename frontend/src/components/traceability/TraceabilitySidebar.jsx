import ThemeToggle from './ThemeToggle'

function TraceabilitySidebar({
  darkMode,
  setDarkMode,
  projectId,
}) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-icon">
          ⌘
        </div>

        <div className="brand-text">
          DesignTrace <span>AI</span>
        </div>
      </div>

      <div className="project-box">
        <p className="project-label">
          CURRENT PROJECT
        </p>

        <div className="project-select">
          <span>
            {projectId || 'No project analyzed'}
          </span>

          <span>⌄</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        <button type="button">
          <span>▦</span>
          Dashboard
        </button>

        <button type="button">
          <span>□</span>
          Projects
        </button>

        <button type="button">
          <span>▤</span>
          Requirements
        </button>

        <button type="button">
          <span>◇</span>
          Design Workspace
        </button>

        <button type="button">
          <span>⚙</span>
          Architecture Design
        </button>

        <button type="button">
          <span>▱</span>
          Database Design
        </button>

        <button type="button">
          <span>▣</span>
          API & Component Design
        </button>

        <button
          type="button"
          className="active"
        >
          <span>⌁</span>
          Traceability
        </button>

        <button type="button">
          <span>♢</span>
          Quality Evaluation
        </button>

        <button type="button">
          <span>▱</span>
          ADR Records
        </button>

        <button type="button">
          <span>▥</span>
          Reports
        </button>

        <button type="button">
          <span>⚙</span>
          Settings
        </button>
      </nav>

      <div className="sidebar-bottom">
        <div className="user-box">
          <div className="user-avatar">
            AR
          </div>

          <div>
            <p className="user-name">
              Alex Rivera
            </p>

            <p className="user-role">
              Lead Architect
            </p>
          </div>
        </div>

        <ThemeToggle
          darkMode={darkMode}
          setDarkMode={setDarkMode}
        />
      </div>
    </aside>
  )
}

export default TraceabilitySidebar