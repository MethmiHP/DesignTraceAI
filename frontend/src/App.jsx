import { useState } from "react";
import {
  LayoutDashboard,
  FolderKanban,
  ClipboardList,
  Workflow,
  Database,
  Blocks,
  GitBranch,
  ShieldCheck,
  FileText,
  Settings,
  Menu,
  X,
  ChevronRight,
  CircleDot,
} from "lucide-react";

import DatabaseDesignPage from "./components/database/DatabaseDesignPage";
import "./App.css";

const menuItems = [
  {
    title: "Workspace",
    items: [
      { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
      { id: "projects", label: "Projects", icon: FolderKanban },
    ],
  },
  {
    title: "Design Modules",
    items: [
      { id: "requirements", label: "Requirements", icon: ClipboardList },
      { id: "architecture", label: "Architecture Design", icon: Workflow },
      { id: "database", label: "Database Design", icon: Database },
      { id: "api", label: "API & Component Design", icon: Blocks },
      { id: "traceability", label: "Traceability", icon: GitBranch },
      { id: "quality", label: "Quality Evaluation", icon: ShieldCheck },
      { id: "reports", label: "Design Reports", icon: FileText },
    ],
  },
];

function App() {
  const [activePage, setActivePage] = useState("database");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const currentItem = menuItems
    .flatMap((group) => group.items)
    .find((item) => item.id === activePage);

  return (
    <div className="dt-app">
      <aside className={`dt-sidebar ${sidebarOpen ? "is-open" : ""}`}>
        <div className="dt-brand">
          <div className="dt-brand-mark">D</div>
          <div className="dt-brand-copy">
            <strong>DesignTrace <span>AI</span></strong>
            <small>Design Intelligence Platform</small>
          </div>
          <button
            className="dt-mobile-close"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close sidebar"
          >
            <X size={20} />
          </button>
        </div>

        <div className="dt-sidebar-project">
          <span className="dt-sidebar-caption">CURRENT PROJECT</span>
          <div className="dt-project-chip">
            <div className="dt-project-avatar">H</div>
            <div>
              <strong>Hospital Management</strong>
              <small>Module demonstration</small>
            </div>
          </div>
        </div>

        <nav className="dt-nav">
          {menuItems.map((group) => (
            <div className="dt-nav-group" key={group.title}>
              <div className="dt-nav-title">{group.title}</div>
              {group.items.map((item) => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.id}
                    className={`dt-nav-link ${
                      activePage === item.id ? "active" : ""
                    }`}
                    onClick={() => {
                      setActivePage(item.id);
                      setSidebarOpen(false);
                    }}
                  >
                    <Icon size={17} strokeWidth={1.9} />
                    <span>{item.label}</span>
                    {activePage === item.id && (
                      <ChevronRight size={15} className="dt-nav-chevron" />
                    )}
                  </button>
                );
              })}
            </div>
          ))}
        </nav>

        <div className="dt-sidebar-bottom">
          <div className="dt-demo-status">
            <CircleDot size={15} />
            <div>
              <strong>Research prototype</strong>
              <small>Standalone module demo</small>
            </div>
          </div>
          <button
            className="dt-settings-link"
            onClick={() => setActivePage("settings")}
          >
            <Settings size={17} />
            Settings
          </button>
        </div>
      </aside>

      {sidebarOpen && (
        <button
          className="dt-backdrop"
          aria-label="Close navigation"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <div className="dt-main">
        <header className="dt-topbar">
          <div className="dt-topbar-left">
            <button
              className="dt-menu-button"
              onClick={() => setSidebarOpen(true)}
              aria-label="Open navigation"
            >
              <Menu size={22} />
            </button>
            <span>Design Workspace</span>
            <ChevronRight size={15} />
            <strong>{currentItem?.label || "Settings"}</strong>
          </div>

          <div className="dt-topbar-right">
            <span className="dt-header-status">
              <span className="dt-status-dot" />
              Demo Environment
            </span>
            <div className="dt-user-avatar">DT</div>
          </div>
        </header>

        <main className="dt-content">
          {activePage === "database" ? (
            <DatabaseDesignPage />
          ) : (
            <div className="dt-coming-soon">
              <div className="dt-coming-icon">
                {currentItem ? (
                  <currentItem.icon size={30} />
                ) : (
                  <Settings size={30} />
                )}
              </div>
              <span className="dt-eyebrow">FUTURE INTEGRATION</span>
              <h1>{currentItem?.label || "Settings"}</h1>
              <p>
                This workspace belongs to the complete DesignTrace AI
                system. It is not connected in the current standalone
                Database Design Module demonstration.
              </p>
              <button
                className="dt-primary-button"
                onClick={() => setActivePage("database")}
              >
                Open Database Design
                <ChevronRight size={16} />
              </button>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
