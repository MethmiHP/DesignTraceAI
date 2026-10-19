import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  useLocation,
  useNavigate,
} from "react-router-dom";

import RequirementSummary from "../../components/requirement-analysis/RequirementSummary";
import RequirementTable from "../../components/requirement-analysis/RequirementTable";


const RESULT_STORAGE_KEY =
  "designtrace-requirement-result";

const DRAFT_STORAGE_KEY =
  "designtrace-requirement-draft";


export default function RequirementAnalysisResultsPage() {
  const navigate = useNavigate();
  const location = useLocation();


  // ========================================================
  // RESTORE RESULT
  // ========================================================

  const getStoredResult = () => {
    if (location.state?.result) {
      return location.state.result;
    }

    try {
      const storedResult =
        sessionStorage.getItem(
          RESULT_STORAGE_KEY
        );

      if (storedResult) {
        return JSON.parse(
          storedResult
        );
      }
    } catch (error) {
      console.error(
        "Unable to restore analysis result:",
        error
      );
    }

    return null;
  };


  // ========================================================
  // RESTORE INPUT DRAFT
  // ========================================================

  const getStoredDraft = () => {
    if (location.state?.draft) {
      return location.state.draft;
    }

    try {
      const storedDraft =
        sessionStorage.getItem(
          DRAFT_STORAGE_KEY
        );

      if (storedDraft) {
        return JSON.parse(
          storedDraft
        );
      }
    } catch (error) {
      console.error(
        "Unable to restore requirement draft:",
        error
      );
    }

    return null;
  };


  const result = getStoredResult();

  const draft = getStoredDraft();


  // ========================================================
  // THEME
  // ========================================================

  const [theme, setTheme] = useState(() => {
    return (
      localStorage.getItem(
        "designtrace-theme"
      ) || "dark"
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


  // ========================================================
  // ASR REQUIREMENTS
  // ========================================================

  const asrRequirements = useMemo(() => {
    if (!result?.requirements) {
      return [];
    }

    return result.requirements.filter(
      (requirement) =>
        requirement.asr
    );
  }, [result]);


  // ========================================================
  // QUALITY ISSUES
  // ========================================================

  const attentionRequirements = useMemo(() => {
    if (!result?.requirements) {
      return [];
    }

    return result.requirements.filter(
      (requirement) =>
        requirement
          .quality_issues
          ?.ambiguous ||

        requirement
          .quality_issues
          ?.incomplete ||

        requirement
          .quality_issues
          ?.conflicting ||

        requirement
          .quality_issues
          ?.potentially_missing
    );
  }, [result]);


  // ========================================================
  // AVERAGE CONFIDENCE
  // ========================================================

  const averageConfidence = useMemo(() => {
    if (
      !result?.requirements ||
      result.requirements.length === 0
    ) {
      return 0;
    }

    const total =
      result.requirements.reduce(
        (
          sum,
          requirement
        ) =>
          sum +
          Number(
            requirement.confidence ||
              0
          ),
        0
      );

    return (
      total /
      result.requirements.length
    );
  }, [result]);


  // ========================================================
  // EDIT REQUIREMENTS
  // ========================================================

  const handleEditRequirements = () => {
    navigate(
      "/requirements",
      {
        state: {
          draft,
        },
      }
    );
  };


  // ========================================================
  // EXPORT ANALYSIS
  // ========================================================

  const handleExportAnalysis = () => {
    if (!result) {
      return;
    }

    const content =
      JSON.stringify(
        result,
        null,
        2
      );

    const blob = new Blob(
      [content],
      {
        type:
          "application/json",
      }
    );

    const url =
      URL.createObjectURL(
        blob
      );

    const link =
      document.createElement(
        "a"
      );

    link.href = url;

    link.download =
      `${result.project_id}_requirement_analysis.json`;

    document.body.appendChild(
      link
    );

    link.click();

    document.body.removeChild(
      link
    );

    URL.revokeObjectURL(
      url
    );
  };


  // ========================================================
  // EXPORT SRS
  // ========================================================

  const handleExportSRS = () => {
    if (!result?.generated_srs) {
      return;
    }

    const blob = new Blob(
      [
        result.generated_srs,
      ],
      {
        type:
          "text/plain;charset=utf-8",
      }
    );

    const url =
      URL.createObjectURL(
        blob
      );

    const link =
      document.createElement(
        "a"
      );

    link.href = url;

    link.download =
      `${result.project_id}_SRS.txt`;

    document.body.appendChild(
      link
    );

    link.click();

    document.body.removeChild(
      link
    );

    URL.revokeObjectURL(
      url
    );
  };


  // ========================================================
  // NO RESULT
  // ========================================================

  if (!result) {
    return (
      <div className="designtrace-layout">

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

            <button
              type="button"
            >
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

          </nav>


          <div className="sidebar-bottom">

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
                onClick={
                  toggleTheme
                }
              >
                <span />
              </button>

            </div>

          </div>

        </aside>


        <main className="requirement-workspace">

          <header className="workspace-header">

            <div>

              <h1>
                Requirement Analysis Results
              </h1>

              <p>
                No analysis result is available.
              </p>

            </div>


            <button
              type="button"
              className="header-theme-toggle"
              onClick={
                toggleTheme
              }
            >
              {theme === "dark"
                ? "☀ Light"
                : "☾ Dark"}
            </button>

          </header>


          <div className="workspace-body">

            <section className="requirement-card">

              <p>
                Please run requirement
                analysis first.
              </p>

              <button
                type="button"
                className="analyze-button"
                onClick={() =>
                  navigate(
                    "/requirements"
                  )
                }
              >
                Back to Requirement Input
              </button>

            </section>

          </div>

        </main>

      </div>
    );
  }


  return (
    <div className="designtrace-layout">

      {/* ==================================================
          LEFT SIDEBAR
          ================================================== */}

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
            {result.project_id}
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
              onClick={
                toggleTheme
              }
              aria-label="Toggle theme"
            >
              <span />
            </button>

          </div>

        </div>

      </aside>


      {/* ==================================================
          RESULTS WORKSPACE
          ================================================== */}

      <main className="requirement-workspace">

        <header className="workspace-header">

          <div>

            <h1>
              Requirement Analysis Results
            </h1>

            <p>
              Agent has analyzed your requirements
              and identified requirement types,
              quality issues, and architecturally
              significant requirements.
            </p>

          </div>


          <div className="workspace-header-actions">

            <div className="workflow-steps">

              <div className="workflow-step completed">
                <span>✓</span>
                Project Info
              </div>

              <div className="workflow-line" />

              <div className="workflow-step completed">
                <span>✓</span>
                Requirements
              </div>

              <div className="workflow-line" />

              <div className="workflow-step active">
                <span>3</span>
                Analysis
              </div>

              <div className="workflow-line" />

              <div className="workflow-step">
                <span>4</span>
                Review
              </div>

            </div>


            <button
              type="button"
              className="header-theme-toggle"
              onClick={
                toggleTheme
              }
            >
              {theme === "dark"
                ? "☀ Light"
                : "☾ Dark"}
            </button>

          </div>

        </header>


        {/* ==================================================
            RESULTS CONTENT
            ================================================== */}

        <div className="results-layout">


          {/* MAIN COLUMN */}

          <div className="results-main-column">

            <RequirementSummary
              result={result}
            />


            <RequirementTable
              requirements={
                result.requirements
              }
            />


            {/* GENERATED SRS */}

            <section className="results-srs-section">

              <div className="section-heading">

                <div>

                  <h2>
                    Generated SRS
                  </h2>

                  <p>
                    Structured Software Requirements
                    Specification generated from the
                    analyzed requirements.
                  </p>

                </div>


                <button
                  type="button"
                  className="secondary-action-button"
                  onClick={
                    handleExportSRS
                  }
                >
                  Export SRS
                </button>

              </div>


              <div className="generated-srs-panel">

                <pre>
                  {
                    result.generated_srs
                  }
                </pre>

              </div>

            </section>

          </div>


          {/* ==================================================
              RIGHT PANEL
              ================================================== */}

          <aside className="results-right-panel">


            {/* OVERVIEW */}

            <section className="results-side-card">

              <div className="results-side-title">
                Requirements Overview
              </div>


              <div className="overview-circle">

                <div>

                  <strong>
                    {
                      result.summary
                        ?.total_requirements ||
                      0
                    }
                  </strong>

                  <span>
                    Total
                  </span>

                </div>

              </div>


              <div className="overview-legend">

                <div>

                  <span className="legend-dot fr-dot" />

                  Functional

                  <strong>
                    {
                      result.summary
                        ?.functional_requirements ||
                      0
                    }
                  </strong>

                </div>


                <div>

                  <span className="legend-dot nfr-dot" />

                  Non-Functional

                  <strong>
                    {
                      result.summary
                        ?.non_functional_requirements ||
                      0
                    }
                  </strong>

                </div>


                <div>

                  <span className="legend-dot asr-dot" />

                  ASR

                  <strong>
                    {
                      result.summary
                        ?.asr_count ||
                      0
                    }
                  </strong>

                </div>

              </div>

            </section>


            {/* ==================================================
                QUALITY SUMMARY
                ================================================== */}

            <section className="results-side-card">

              <div className="results-side-title">
                Quality Summary
              </div>


              <div className="quality-summary-grid">

                <div>

                  <span>
                    Avg. Confidence
                  </span>

                  <strong>
                    {(
                      averageConfidence *
                      100
                    ).toFixed(0)}
                    %
                  </strong>

                </div>


                <div>

                  <span>
                    Ambiguous
                  </span>

                  <strong>
                    {
                      result.summary
                        ?.ambiguous_count ||
                      0
                    }
                  </strong>

                </div>


                <div>

                  <span>
                    Incomplete
                  </span>

                  <strong>
                    {
                      result.summary
                        ?.incomplete_count ||
                      0
                    }
                  </strong>

                </div>


                <div>

                  <span>
                    Conflicts
                  </span>

                  <strong>
                    {
                      result.summary
                        ?.conflict_count ||
                      0
                    }
                  </strong>

                </div>


                <div>

                  <span>
                    Potentially Missing
                  </span>

                  <strong>
                    {
                      result.summary
                        ?.potentially_missing_count ||
                      0
                    }
                  </strong>

                </div>

              </div>

            </section>


            {/* ==================================================
                ASR SECTION
                ================================================== */}

            <section className="results-side-card">

              <div className="results-side-title">
                Architecturally Significant
              </div>


              <div className="attention-list">

                {asrRequirements.length ===
                  0 && (

                  <div className="attention-empty">
                    No architecturally significant
                    requirements identified.
                  </div>

                )}


                {asrRequirements
                  .slice(0, 5)
                  .map(
                    (
                      requirement
                    ) => (

                      <div
                        key={
                          requirement
                            .requirement_id
                        }
                        className="asr-attention-item"
                      >

                        <strong>
                          {
                            requirement
                              .requirement_id
                          }
                        </strong>

                        <span>
                          {
                            requirement
                              .normalized_statement
                          }
                        </span>

                        {requirement
                          .quality_attribute && (

                          <small>
                            {
                              requirement
                                .quality_attribute
                            }
                          </small>

                        )}

                      </div>

                    )
                  )}


                {asrRequirements.length >
                  5 && (

                  <div className="attention-more">

                    +{" "}
                    {
                      asrRequirements.length -
                      5
                    }{" "}
                    more ASRs

                  </div>

                )}

              </div>

            </section>


            {/* ==================================================
                REQUIRES ATTENTION
                ================================================== */}

            <section className="results-side-card">

              <div className="results-side-title">
                Requires Attention
              </div>


              <div className="attention-list">

                {attentionRequirements.length ===
                  0 && (

                  <div className="attention-empty">
                    No detected quality issues
                    require attention.
                  </div>

                )}


                {attentionRequirements.map(
                  (
                    requirement
                  ) => {

                    const issues = [];


                    if (
                      requirement
                        .quality_issues
                        ?.ambiguous
                    ) {
                      issues.push(
                        "Ambiguous"
                      );
                    }


                    if (
                      requirement
                        .quality_issues
                        ?.incomplete
                    ) {
                      issues.push(
                        "Incomplete"
                      );
                    }


                    if (
                      requirement
                        .quality_issues
                        ?.conflicting
                    ) {
                      issues.push(
                        "Conflict"
                      );
                    }


                    if (
                      requirement
                        .quality_issues
                        ?.potentially_missing
                    ) {
                      issues.push(
                        "Potentially Missing"
                      );
                    }


                    return (
                      <div
                        key={
                          requirement
                            .requirement_id
                        }
                        className="attention-item"
                      >

                        <div className="attention-item-header">

                          <strong>
                            {
                              requirement
                                .requirement_id
                            }
                          </strong>


                          <span className="attention-issue-label">
                            {
                              issues.join(
                                ", "
                              )
                            }
                          </span>

                        </div>


                        <span>
                          {
                            requirement
                              .normalized_statement
                          }
                        </span>


                        {requirement
                          .issue_details
                          ?.length >
                          0 && (

                          <div className="attention-detail">

                            {requirement
                              .issue_details[0]
                              ?.evidence && (

                              <small>

                                <strong>
                                  Evidence:
                                </strong>{" "}

                                {
                                  requirement
                                    .issue_details[0]
                                    .evidence
                                }

                              </small>

                            )}


                            {requirement
                              .issue_details[0]
                              ?.recommendation && (

                              <small className="attention-recommendation">

                                <strong>
                                  Recommendation:
                                </strong>{" "}

                                {
                                  requirement
                                    .issue_details[0]
                                    .recommendation
                                }

                              </small>

                            )}

                          </div>

                        )}

                      </div>
                    );
                  }
                )}

              </div>

            </section>

          </aside>

        </div>


        {/* ==================================================
            BOTTOM ACTION BAR
            ================================================== */}

        <div className="results-bottom-bar">

          <button
            type="button"
            className="secondary-action-button"
            onClick={
              handleEditRequirements
            }
          >
            ← Edit Requirements
          </button>


          <div className="results-bottom-actions">

            <button
              type="button"
              className="secondary-action-button"
              onClick={
                handleExportAnalysis
              }
            >
              Export Analysis
            </button>


            <button
              type="button"
              className="gold-action-button"
              onClick={
                handleExportSRS
              }
            >
              Export SRS
            </button>


            <button
              type="button"
              className="analyze-button"
            >
              Continue to Design Workspace →
            </button>

          </div>

        </div>

      </main>

    </div>
  );
}