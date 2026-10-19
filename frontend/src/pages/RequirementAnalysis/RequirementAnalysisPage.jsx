// import { useEffect, useState } from "react";

// import RequirementInput from "../../components/requirement-analysis/RequirementInput";

// export default function RequirementAnalysisPage() {
//   const [theme, setTheme] = useState(() => {
//     return localStorage.getItem("designtrace-theme") || "dark";
//   });

//   useEffect(() => {
//     document.documentElement.setAttribute(
//       "data-theme",
//       theme
//     );

//     localStorage.setItem(
//       "designtrace-theme",
//       theme
//     );
//   }, [theme]);

//   const toggleTheme = () => {
//     setTheme((currentTheme) =>
//       currentTheme === "dark"
//         ? "light"
//         : "dark"
//     );
//   };

//   return (
//     <div className="requirement-page">
//       <header className="requirement-topbar">
//         <div>
//           <h1>Requirement Analysis</h1>

//           <p>
//             Analyze software requirements using AI-assisted
//             extraction, classification, quality analysis,
//             and ASR detection.
//           </p>
//         </div>

//         <button
//           className="theme-toggle"
//           type="button"
//           onClick={toggleTheme}
//         >
//           {theme === "dark"
//             ? "☀ Light"
//             : "☾ Dark"}
//         </button>
//       </header>

//       <main className="requirement-content">
//         <RequirementInput />
//       </main>
//     </div>
//   );
// }

import { useEffect, useState } from "react";

import RequirementInput from "../../components/requirement-analysis/RequirementInput";


export default function RequirementAnalysisPage() {
  const [theme, setTheme] = useState(() => {
    return (
      localStorage.getItem("designtrace-theme") ||
      "dark"
    );
  });


  useEffect(() => {
    document.documentElement.setAttribute(
      "data-theme",
      theme
    );

    localStorage.setItem(
      "designtrace-theme",
      theme
    );
  }, [theme]);


  const toggleTheme = () => {
    setTheme((currentTheme) =>
      currentTheme === "dark"
        ? "light"
        : "dark"
    );
  };


  return (
    <div className="designtrace-layout">

      {/* ==============================
          LEFT SIDEBAR
          ============================== */}

      <aside className="designtrace-sidebar">

        <div className="sidebar-brand">

          <div className="sidebar-logo">
            DT
          </div>

          <div>
            <strong>
              DesignTrace
            </strong>

            <span>
              AI
            </span>
          </div>

        </div>


        <div className="sidebar-project">

          <span>
            CURRENT PROJECT
          </span>

          <strong>
            Requirement Analysis
          </strong>

        </div>


        <nav className="sidebar-navigation">

          <button type="button">
            <span>▦</span>
            Dashboard
          </button>

          <button
            type="button"
            className="active"
          >
            <span>◫</span>
            Requirements
          </button>

          <button type="button">
            <span>◇</span>
            Design Workspace
          </button>

          <button type="button">
            <span>▤</span>
            Database Design
          </button>

          <button type="button">
            <span>⌘</span>
            API & Component Design
          </button>

          <button type="button">
            <span>↗</span>
            Traceability
          </button>

          <button type="button">
            <span>✓</span>
            Quality Evaluation
          </button>

          <button type="button">
            <span>▣</span>
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

          <div className="sidebar-user">

            <div className="sidebar-avatar">
              D
            </div>

            <div>
              <strong>
                Demo User
              </strong>

              <span>
                Requirement Analyst
              </span>
            </div>

          </div>


          <div className="sidebar-theme-row">

            <span>
              {theme === "dark"
                ? "Dark Mode"
                : "Light Mode"}
            </span>

            <button
              type="button"
              className={
                theme === "dark"
                  ? "theme-switch active"
                  : "theme-switch"
              }
              onClick={toggleTheme}
              aria-label="Toggle theme"
            >
              <span />
            </button>

          </div>

        </div>

      </aside>


      {/* ==============================
          MAIN WORKSPACE
          ============================== */}

      <main className="requirement-workspace">

        <header className="workspace-header">

          <div>

            <h1>
              Requirement Input
            </h1>

            <p>
              Provide your project requirements in
              any of the following ways.
            </p>

          </div>


          <div className="workflow-steps">

            <div className="workflow-step completed">
              <span>✓</span>
              Project Info
            </div>

            <div className="workflow-line" />

            <div className="workflow-step active">
              <span>2</span>
              Requirements
            </div>

            <div className="workflow-line" />

            <div className="workflow-step">
              <span>3</span>
              Analysis
            </div>

            <div className="workflow-line" />

            <div className="workflow-step">
              <span>4</span>
              Review
            </div>

          </div>

        </header>


        <div className="workspace-body">

          <RequirementInput />

        </div>

      </main>

    </div>
  );
}