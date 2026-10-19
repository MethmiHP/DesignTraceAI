import { useEffect, useState } from "react";
import { LayoutDashboard, FolderKanban, ClipboardList, Workflow, Database, Blocks, GitBranch, ShieldCheck, FileText, Settings, Menu, X, ChevronRight, Moon, Sun, CircleDot } from "lucide-react";
import DatabaseDesignPage from "./components/database/DatabaseDesignPage";
import "./App.css";

const groups = [
  { label: "WORKSPACE", items: [["dashboard", "Dashboard", LayoutDashboard], ["projects", "Projects", FolderKanban]] },
  { label: "DESIGN MODULES", items: [["requirements", "Requirements", ClipboardList], ["architecture", "Architecture Design", Workflow], ["database", "Database Design", Database], ["api", "API & Component Design", Blocks], ["traceability", "Traceability", GitBranch], ["quality", "Quality Evaluation", ShieldCheck], ["reports", "Design Reports", FileText]] },
];

export default function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem("designtrace-theme") === "light" ? "light" : "dark");
  const [active, setActive] = useState("database");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [project, setProject] = useState({ id: "TEST-HOSPITAL-AI-001", name: "Hospital Management System" });
  useEffect(() => { localStorage.setItem("designtrace-theme", theme); document.documentElement.setAttribute("data-theme", theme); }, [theme]);
  const current = groups.flatMap(g => g.items).find(item => item[0] === active);
  return <div className="dt-app" data-theme={theme}>
    <aside className={`dt-sidebar ${sidebarOpen ? "is-open" : ""}`}>
      <div className="dt-brand"><div className="dt-brand-mark">⌘</div><div><strong>DesignTrace <span>AI</span></strong><small>DESIGN INTELLIGENCE PLATFORM</small></div><button className="dt-mobile-close" onClick={() => setSidebarOpen(false)} aria-label="Close sidebar"><X size={19}/></button></div>
      <div className="dt-sidebar-project"><span className="dt-sidebar-caption">CURRENT PROJECT</span><div className="dt-project-chip"><div className="dt-project-avatar">{project.name[0] || "D"}</div><div><strong>{project.name}</strong><small>{project.id}</small></div></div></div>
      <nav className="dt-nav">{groups.map(g => <div className="dt-nav-group" key={g.label}><div className="dt-nav-title">{g.label}</div>{g.items.map(([id,label,Icon]) => <button key={id} className={`dt-nav-link ${active === id ? "active" : ""}`} onClick={() => {setActive(id);setSidebarOpen(false)}}><Icon size={17}/><span>{label}</span>{active === id && <ChevronRight size={15} className="dt-nav-chevron"/>}</button>)}</div>)}</nav>
      <div className="dt-sidebar-bottom"><div className="dt-demo-status"><CircleDot size={16}/><span>Research prototype</span></div><button className="dt-settings-link" onClick={() => setActive("settings")}><Settings size={17}/> Settings</button></div>
    </aside>
    {sidebarOpen && <button className="dt-backdrop" aria-label="Close navigation" onClick={() => setSidebarOpen(false)}/>}
    <div className="dt-main"><header className="dt-topbar"><div className="dt-topbar-left"><button className="dt-menu-button" onClick={() => setSidebarOpen(true)} aria-label="Open menu"><Menu size={21}/></button><span>Design workspace</span><ChevronRight size={15}/><strong>{current?.[1] || "Settings"}</strong></div><div className="dt-topbar-right"><button className="dt-theme-button" onClick={() => setTheme(t => t === "dark" ? "light" : "dark")}>{theme === "dark" ? <Sun size={16}/> : <Moon size={16}/>} {theme === "dark" ? "Light theme" : "Dark theme"}</button><span className="dt-header-status"><span className="dt-status-dot"/> Database Module</span><div className="dt-user-avatar">DT</div></div></header>
      <main className="dt-content">{active === "database" ? <DatabaseDesignPage onProjectChange={setProject} /> : <div className="dt-coming-soon"><h1>{current?.[1] || "Settings"}</h1><p>This section is not connected in this standalone Database Design Module frontend.</p><button className="dt-primary-button" onClick={() => setActive("database")}>Open Database Design <ChevronRight size={16}/></button></div>}</main>
    </div>
  </div>;
}
