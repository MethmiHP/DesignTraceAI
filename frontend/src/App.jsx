import { useState } from "react";
import "./App.css";
import { analyzeRequirements } from "./services/requirementService";

function App() {
  const [projectId, setProjectId] = useState("");
  const [description, setDescription] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleAnalyze = async () => {
    if (!projectId.trim() || !description.trim()) {
      setError("Please enter both Project ID and Project Description.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const data = await analyzeRequirements({
        project_id: projectId,
        raw_description: description,
        project_context: {
          domain: "",
          system_type: "",
          primary_users: [],
          constraints: [],
          technology_preferences: [],
        },
      });

      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLoadDemo = () => {
    setError("");
    setProjectId("DEMO-001");

    setDescription(
      "Patients shall be able to book appointments online. " +
        "Patient information shall be secure. " +
        "The system shall respond within 2 seconds."
    );

    setResult({
      requirements: [
        {
          requirement_id: "REQ-001",
          original_text:
            "Patients shall be able to book appointments online.",
          normalized_statement:
            "Patients shall be able to book appointments online.",
          requirement_type: "FR",
          quality_attribute: null,
          asr: false,
          confidence: 0.9949,
          quality_issues: {
            ambiguous: false,
            incomplete: false,
            conflicting: false,
            potentially_missing: false,
          },
        },
        {
          requirement_id: "REQ-002",
          original_text:
            "Patient information shall be secure.",
          normalized_statement:
            "Patient information shall be protected from unauthorized access.",
          requirement_type: "NFR",
          quality_attribute: "Security",
          asr: true,
          confidence: 0.722,
          quality_issues: {
            ambiguous: true,
            incomplete: true,
            conflicting: false,
            potentially_missing: false,
          },
        },
        {
          requirement_id: "REQ-003",
          original_text:
            "The system shall respond within 2 seconds.",
          normalized_statement:
            "The system shall respond within 2 seconds.",
          requirement_type: "NFR",
          quality_attribute: "Performance",
          asr: true,
          confidence: 0.4014,
          quality_issues: {
            ambiguous: false,
            incomplete: true,
            conflicting: false,
            potentially_missing: false,
          },
        },
      ],

      summary: {
        total_requirements: 3,
        functional_requirements: 1,
        non_functional_requirements: 2,
        architecturally_significant_requirements: 2,
        ambiguous_count: 1,
        incomplete_count: 2,
        conflict_count: 0,
        potentially_missing_count: 0,
      },

      generated_srs: `SOFTWARE REQUIREMENTS SPECIFICATION

1. Functional Requirements

REQ-001
Patients shall be able to book appointments online.

2. Non-Functional Requirements

REQ-002
Patient information shall be protected from unauthorized access.
Quality Attribute: Security
Architecturally Significant: Yes

REQ-003
The system shall respond within 2 seconds.
Quality Attribute: Performance
Architecturally Significant: Yes

3. Quality Review

REQ-002 requires clarification regarding the exact security controls.

REQ-003 requires clarification regarding the operation and load conditions under which the two-second response time applies.`,

      validation: {
        valid: true,
        issues: [],
      },
    });
  };

  const formatConfidence = (value) => {
    if (value === null || value === undefined) {
      return "-";
    }

    return `${(Number(value) * 100).toFixed(1)}%`;
  };

  return (
    <div className="app">
      <header className="header">
        <h1>DesignTrace AI</h1>
        <p>AI-Assisted Requirement Analysis</p>
      </header>

      <main className="container">
        <section className="card input-card">
          <h2>Project Requirements</h2>

          <label>Project ID</label>

          <input
            type="text"
            placeholder="Example: P001"
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
          />

          <label>Project Description</label>

          <textarea
            rows="12"
            placeholder="Enter the project requirements here..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />

          <button
            type="button"
            onClick={handleAnalyze}
            disabled={loading}
          >
            {loading ? "Analyzing..." : "Analyze Requirements"}
          </button>

          <button
            type="button"
            className="demo-button"
            onClick={handleLoadDemo}
            disabled={loading}
          >
            Load Demo Result
          </button>

          {error && (
            <div className="error-box">
              <strong>Request failed</strong>
              <p>{error}</p>
            </div>
          )}
        </section>

        <section className="card results-card">
          <h2>Analysis Results</h2>

          {!result && !loading && (
            <div className="empty-state">
              <p>Analysis results will appear here.</p>
            </div>
          )}

          {loading && (
            <div className="empty-state">
              <p>Analyzing requirements...</p>
            </div>
          )}

          {result && (
            <>
              {result.summary && (
                <div className="summary-grid">
                  <div className="summary-item">
                    <span>Total</span>
                    <strong>
                      {result.summary.total_requirements ?? "-"}
                    </strong>
                  </div>

                  <div className="summary-item">
                    <span>Functional</span>
                    <strong>
                      {result.summary.functional_requirements ?? "-"}
                    </strong>
                  </div>

                  <div className="summary-item">
                    <span>Non-Functional</span>
                    <strong>
                      {result.summary.non_functional_requirements ?? "-"}
                    </strong>
                  </div>

                  <div className="summary-item">
                    <span>ASRs</span>
                    <strong>
                      {result.summary
                        .architecturally_significant_requirements ?? "-"}
                    </strong>
                  </div>
                </div>
              )}

              <div className="requirements-list">
                {result.requirements?.map((requirement) => (
                  <div
                    className="requirement-card"
                    key={requirement.requirement_id}
                  >
                    <div className="requirement-header">
                      <h3>{requirement.requirement_id}</h3>

                      <span
                        className={`type-badge ${
                          requirement.requirement_type === "FR"
                            ? "fr"
                            : "nfr"
                        }`}
                      >
                        {requirement.requirement_type}
                      </span>
                    </div>

                    <p className="requirement-text">
                      {requirement.normalized_statement}
                    </p>

                    <div className="meta-grid">
                      <div>
                        <span className="meta-label">
                          Quality Attribute
                        </span>
                        <span>
                          {requirement.quality_attribute || "-"}
                        </span>
                      </div>

                      <div>
                        <span className="meta-label">ASR</span>
                        <span>
                          {requirement.asr ? "Yes" : "No"}
                        </span>
                      </div>

                      <div>
                        <span className="meta-label">
                          Confidence
                        </span>
                        <span>
                          {formatConfidence(requirement.confidence)}
                        </span>
                      </div>
                    </div>

                    <div className="quality-section">
                      <h4>Quality Issues</h4>

                      <div className="issue-badges">
                        <span
                          className={
                            requirement.quality_issues?.ambiguous
                              ? "issue-badge issue"
                              : "issue-badge clear"
                          }
                        >
                          Ambiguous:{" "}
                          {requirement.quality_issues?.ambiguous
                            ? "Yes"
                            : "No"}
                        </span>

                        <span
                          className={
                            requirement.quality_issues?.incomplete
                              ? "issue-badge issue"
                              : "issue-badge clear"
                          }
                        >
                          Incomplete:{" "}
                          {requirement.quality_issues?.incomplete
                            ? "Yes"
                            : "No"}
                        </span>

                        <span
                          className={
                            requirement.quality_issues?.conflicting
                              ? "issue-badge issue"
                              : "issue-badge clear"
                          }
                        >
                          Conflict:{" "}
                          {requirement.quality_issues?.conflicting
                            ? "Yes"
                            : "No"}
                        </span>

                        <span
                          className={
                            requirement.quality_issues?.potentially_missing
                              ? "issue-badge issue"
                              : "issue-badge clear"
                          }
                        >
                          Potentially Missing:{" "}
                          {requirement.quality_issues?.potentially_missing
                            ? "Yes"
                            : "No"}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {result.generated_srs && (
                <div className="srs-section">
                  <h3>Generated SRS</h3>
                  <pre>{result.generated_srs}</pre>
                </div>
              )}
            </>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;