import { useState } from "react";

import { analyzeArchitecture } from "../services/architectureService";

import ArchitectureDiagram from "../components/architecture/ArchitectureDiagram";



const createRequirement = (

  requirementId,

  statement,

  requirementType = "functional",

  isAsr = false

) => ({

  requirement_id: requirementId,

  statement,

  requirement_type: requirementType,

  is_asr: isAsr,

});



function ArchitectureDecisionPage() {

  const [theme, setTheme] = useState("dark");

  const [projectId, setProjectId] = useState("BANKING-ARCH-002");



  const [requirements, setRequirements] = useState([

    createRequirement(

      "FR-001",

      "Users shall be able to create and manage their bank accounts.",

      "functional",

      false

    ),

    createRequirement(

      "FR-002",

      "Users shall be able to transfer money between accounts.",

      "functional",

      false

    ),

    createRequirement(

      "FR-003",

      "Users shall be able to view their transaction history.",

      "functional",

      false

    ),

    createRequirement(

      "FR-004",

      "The system shall generate downloadable monthly account statements for users.",

      "functional",

      false

    ),

    createRequirement(

      "NFR-001",

      "All financial transactions must be encrypted in transit and protected against unauthorized access.",

      "non_functional",

      true

    ),

    createRequirement(

      "NFR-002",

      "The platform must remain available 99.99% of the time and automatically recover from service failures.",

      "non_functional",

      true

    ),

    createRequirement(

      "NFR-003",

      "Money transfer requests must be processed within 500 milliseconds under normal operating conditions.",

      "non_functional",

      true

    ),

    createRequirement(

      "NFR-004",

      "The system shall support up to 20,000 simultaneous users during peak banking hours.",

      "non_functional",

      true

    ),

  ]);



  const [result, setResult] = useState(null);

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  const [activeTab, setActiveTab] = useState("overview");



  const identifiedAsrs = requirements.filter(

    (requirement) => requirement.is_asr

  );



  const updateRequirement = (index, field, value) => {

    const updated = [...requirements];



    updated[index] = {

      ...updated[index],

      [field]: value,

    };



    setRequirements(updated);

  };



  const addRequirement = () => {

    const nextNumber = requirements.length + 1;



    setRequirements([

      ...requirements,

      createRequirement(

        `REQ-${String(nextNumber).padStart(3, "0")}`,

        "",

        "functional",

        false

      ),

    ]);

  };



  const removeRequirement = (index) => {

    if (requirements.length === 1) {

      return;

    }



    setRequirements(

      requirements.filter(

        (_, currentIndex) => currentIndex !== index

      )

    );

  };



  const validateInput = () => {

    if (!projectId.trim()) {

      return "Project ID is required.";

    }



    if (requirements.length === 0) {

      return "Add at least one project requirement.";

    }



    const cleanedIds = requirements.map((requirement) =>

      requirement.requirement_id.trim()

    );



    if (cleanedIds.some((id) => !id)) {

      return "Every requirement must have a requirement ID.";

    }



    if (new Set(cleanedIds).size !== cleanedIds.length) {

      return "Requirement IDs must be unique.";

    }



    if (

      requirements.some(

        (requirement) => !requirement.statement.trim()

      )

    ) {

      return "Every requirement must have a statement.";

    }



    if (identifiedAsrs.length === 0) {

      return "Mark at least one requirement as an ASR.";

    }



    return "";

  };



  const handleAnalyze = async () => {

    const validationError = validateInput();



    if (validationError) {

      setError(validationError);

      return;

    }



    setLoading(true);

    setError("");

    setResult(null);

    setActiveTab("overview");



    try {

      const payload = {

        project_id: projectId.trim(),



        requirements: requirements.map(

          ({

            requirement_id,

            statement,

            requirement_type,

          }) => ({

            requirement_id: requirement_id.trim(),

            statement: statement.trim(),

            requirement_type,

          })

        ),



        asrs: identifiedAsrs.map(

          ({ requirement_id, statement }) => ({

            requirement_id: requirement_id.trim(),

            statement: statement.trim(),

          })

        ),

      };



      const data = await analyzeArchitecture(payload, 5);

      setResult(data);

    } catch (err) {

      setError(err.message);

    } finally {

      setLoading(false);

    }

  };



  const recommendation = result?.result?.recommendation;

  const evaluations =

    result?.scoring?.architecture_evaluations || [];

  const classifications =

    result?.classification?.classifications || [];

  const qualityProfile =

    result?.classification?.quality_profile || {};

  const evidence = result?.retrieval?.evidence || [];

  const design = result?.result?.design;



  return (

    <div className={"architecture-page " + theme + "-theme"}>
      <div className="designtrace-shell">
        <aside className="designtrace-sidebar">
          <div className="sidebar-brand">
            <div className="sidebar-brand-icon">⌘</div>
            <div className="sidebar-brand-text">
              <span>DesignTrace</span>
              <strong>AI</strong>
            </div>
          </div>

          <div className="sidebar-section-label">
            DESIGN WORKSPACE
          </div>

          <nav className="sidebar-nav" aria-label="Design workspace navigation">
            <button type="button" className="sidebar-nav-item">
              <span className="sidebar-nav-icon">▤</span>
              <span>Design Context</span>
            </button>

            <button
              type="button"
              className="sidebar-nav-item active"
              aria-current="page"
            >
              <span className="sidebar-nav-icon">◇</span>
              <span>Architecture Decision</span>
            </button>

            <button type="button" className="sidebar-nav-item">
              <span className="sidebar-nav-icon">▱</span>
              <span>Database Design</span>
            </button>

            <button type="button" className="sidebar-nav-item">
              <span className="sidebar-nav-icon">⌘</span>
              <span>API & Component Design</span>
            </button>

            <button type="button" className="sidebar-nav-item">
              <span className="sidebar-nav-icon">↯</span>
              <span>Traceability</span>
            </button>

            <button type="button" className="sidebar-nav-item">
              <span className="sidebar-nav-icon">✓</span>
              <span>Quality Evaluation</span>
            </button>

            <button type="button" className="sidebar-nav-item">
              <span className="sidebar-nav-icon">▣</span>
              <span>ADR Records</span>
            </button>
          </nav>

          <div className="sidebar-footer">
            <div className="sidebar-footer-dot" />
            <div>
              <strong>Architecture Module</strong>
              <span>M7.3 workspace</span>
            </div>
          </div>
        </aside>

        <div className="designtrace-content">
          <header className="module-header">
            <div>
              <div className="module-breadcrumb">
                Design workspace / Architecture decision
              </div>
              <h1>Architecture Decision</h1>
              <p>
                Analyse requirements, compare architecture alternatives,
                retrieve supporting evidence, and generate a traceable
                high-level design.
              </p>
            </div>

            <div className="module-header-actions">
              <button
                type="button"
                className="theme-toggle"
                onClick={() =>
                  setTheme((currentTheme) =>
                    currentTheme === "dark" ? "light" : "dark"
                  )
                }
                aria-label={
                    theme === "dark"
                    ? "Switch to light theme"
                    : "Switch to dark theme"
                }
              >
                <span className="theme-toggle-icon">
                  {theme === "dark" ? "☀" : "☾"}
                </span>
                {theme === "dark" ? "Light theme" : "Dark theme"}
              </button>

              <div className="module-header-badge">
                Architecture Module
              </div>
            </div>
          </header>

          <main className="architecture-container">
<section className="workspace-grid">

          {/* =====================================================

              INPUT PANEL

             ===================================================== */}



          <div className="panel input-panel">

            <div className="panel-label">

              01 / INPUT

            </div>



            <h2>Architecture context</h2>



            <label>Project ID</label>



            <input

              value={projectId}

              onChange={(event) =>

                setProjectId(event.target.value)

              }

            />



            <div className="requirements-header">

              <div>

                <h3>

                  All Architecture-Relevant Requirements

                </h3>



                <p className="section-helper">

                  Functional requirements, non-functional

                  requirements, and constraints supplied by

                  Requirement Analysis.

                </p>

              </div>



              <span>{requirements.length}</span>

            </div>



            {requirements.map(

              (requirement, index) => (

                <div

                  className="requirement-card"

                  key={`${requirement.requirement_id}-${index}`}

                >

                  <div className="requirement-id-row">

                    <input

                      value={

                        requirement.requirement_id

                      }

                      onChange={(event) =>

                        updateRequirement(

                          index,

                          "requirement_id",

                          event.target.value

                        )

                      }

                      placeholder="FR-001"

                    />



                    <select

                      className="requirement-type-select"

                      value={

                        requirement.requirement_type

                      }

                      onChange={(event) =>

                        updateRequirement(

                          index,

                          "requirement_type",

                          event.target.value

                        )

                      }

                      aria-label="Requirement type"

                    >

                      <option value="functional">

                        Functional

                      </option>

                      <option value="non_functional">

                        Non-functional

                      </option>

                      <option value="constraint">

                        Constraint

                      </option>

                      <option value="other">

                        Other

                      </option>

                    </select>



                    {requirements.length > 1 && (

                      <button

                        type="button"

                        className="remove-button"

                        onClick={() =>

                          removeRequirement(index)

                        }

                        aria-label="Remove requirement"

                      >

                        ×

                      </button>

                    )}

                  </div>



                  <textarea

                    rows="4"

                    value={requirement.statement}

                    onChange={(event) =>

                      updateRequirement(

                        index,

                        "statement",

                        event.target.value

                      )

                    }

                    placeholder="Enter the requirement statement..."

                  />



                  <label className="asr-checkbox-row">

                    <input

                      type="checkbox"

                      checked={requirement.is_asr}

                      onChange={(event) =>

                        updateRequirement(

                          index,

                          "is_asr",

                          event.target.checked

                        )

                      }

                    />



                    <span>

                      Identified as an Architecturally

                      Significant Requirement (ASR)

                    </span>

                  </label>

                </div>

              )

            )}



            <button

              type="button"

              className="secondary-button"

              onClick={addRequirement}

            >

              + Add requirement

            </button>



            <div className="asr-summary">

              <div className="asr-summary-heading">

                <div>

                  <h3>Identified ASRs</h3>

                  <p>

                    Only these requirements are sent to

                    RoBERTa for quality-attribute analysis.

                  </p>

                </div>



                <span className="asr-count">

                  {identifiedAsrs.length}

                </span>

              </div>



              {identifiedAsrs.length > 0 ? (

                <div className="asr-summary-list">

                  {identifiedAsrs.map((asr) => (

                    <div

                      className="asr-summary-item"

                      key={asr.requirement_id}

                    >

                      <strong>

                        {asr.requirement_id}

                      </strong>



                      <span>

                        {asr.statement ||

                          "Requirement statement not entered yet."}

                      </span>

                    </div>

                  ))}

                </div>

              ) : (

                <p className="asr-empty-message">

                  Mark at least one requirement as an ASR.

                </p>

              )}

            </div>



            <button

              type="button"

              className="primary-button"

              onClick={handleAnalyze}

              disabled={loading}

            >

              {loading

                ? "Analysing Architecture..."

                : "Analyse Architecture"}

            </button>



            {error && (

              <div className="error-box">

                {error}

              </div>

            )}

          </div>



          {/* =====================================================

              OUTPUT PANEL

             ===================================================== */}



          <div className="panel output-panel">

            <div className="panel-label">

              02 / OUTPUT

            </div>



            <h2>Your architecture decision</h2>



            {!result && !loading && (

              <div className="empty-state">

                <div className="empty-icon">

                  ⌘

                </div>



                <h3>

                  From requirements to architecture.

                </h3>



                <p>

                  Add the complete requirement context,

                  identify the ASRs, and run the analysis

                  to explore quality attributes, ranked

                  architectures, evidence, trade-offs,

                  and the generated high-level design.

                </p>

              </div>

            )}



            {loading && (

              <div className="empty-state">

                <h3>Analysing...</h3>



                <p>

                  RoBERTa, deterministic scoring, RAG,

                  and Gemini are processing the project.

                </p>

              </div>

            )}



            {result && (

              <div className="results">

                <div className="recommendation-card">

                  <span className="result-label">

                    {recommendation?.review_required

                      ? "Provisional Architecture"

                      : "Recommended Architecture"}

                  </span>



                  <h3>

                    {recommendation?.selected_style}

                  </h3>



                  <div className="score-badge">

                    Score {recommendation?.score}

                  </div>



                  {recommendation?.review_required && (

                    <div className="review-badge">

                      Human review recommended

                    </div>

                  )}

                </div>



                <div className="result-tabs">

                  <button

                    type="button"

                    className={

                      activeTab === "overview"

                        ? "result-tab active"

                        : "result-tab"

                    }

                    onClick={() =>

                      setActiveTab("overview")

                    }

                  >

                    Overview

                  </button>



                  <button

                    type="button"

                    className={

                      activeTab === "qa"

                        ? "result-tab active"

                        : "result-tab"

                    }

                    onClick={() =>

                      setActiveTab("qa")

                    }

                  >

                    QA Analysis

                  </button>



                  <button

                    type="button"

                    className={

                      activeTab === "alternatives"

                        ? "result-tab active"

                        : "result-tab"

                    }

                    onClick={() =>

                      setActiveTab("alternatives")

                    }

                  >

                    Alternatives

                  </button>



                  <button

                    type="button"

                    className={

                      activeTab === "evidence"

                        ? "result-tab active"

                        : "result-tab"

                    }

                    onClick={() =>

                      setActiveTab("evidence")

                    }

                  >

                    Evidence

                  </button>



                  <button

                    type="button"

                    className={

                      activeTab === "design"

                        ? "result-tab active"

                        : "result-tab"

                    }

                    onClick={() =>

                      setActiveTab("design")

                    }

                  >

                    Design

                  </button>

                </div>



                {activeTab === "overview" && (

                  <div className="tab-content">

                    <section className="result-section">

                      <h3>

                        Recommendation Rationale

                      </h3>



                      <p>

                        {recommendation?.rationale}

                      </p>

                    </section>



                    <section className="result-section">

                      <h3>

                        Key Quality Attributes

                      </h3>



                      <div className="chips">

                        {recommendation?.key_quality_attributes?.map(

                          (attribute) => (

                            <span

                              className="chip"

                              key={attribute}

                            >

                              {attribute}

                            </span>

                          )

                        )}

                      </div>

                    </section>



                    {recommendation?.tied_candidates

                      ?.length > 1 && (

                      <section className="result-section">

                        <h3>Tie Resolution</h3>



                        <div className="chips">

                          {recommendation.tied_candidates.map(

                            (candidate) => (

                              <span

                                className="chip"

                                key={candidate}

                              >

                                {candidate}

                              </span>

                            )

                          )}

                        </div>



                        <p>

                          {recommendation.tie_resolution_reason ||

                            "The available project information was not sufficient to fully resolve the Rank 1 tie."}

                        </p>



                        <div className="tie-status">

                          <span>Tie resolved:</span>

                          <strong>

                            {recommendation.tie_resolved

                              ? "Yes"

                              : "No"}

                          </strong>

                        </div>

                      </section>

                    )}



                    <section className="result-section">

                      <h3>Trade-offs</h3>



                      <ul>

                        {recommendation?.tradeoffs?.map(

                          (tradeoff, index) => (

                            <li key={index}>

                              {tradeoff}

                            </li>

                          )

                        )}

                      </ul>

                    </section>



                    <section className="result-section">

                      <h3>Strengths</h3>



                      <ul>

                        {recommendation?.strengths?.map(

                          (strength, index) => (

                            <li key={index}>

                              {strength}

                            </li>

                          )

                        )}

                      </ul>

                    </section>



                    <section className="result-section">

                      <h3>Accepted Weaknesses</h3>



                      <ul>

                        {recommendation?.weaknesses?.map(

                          (weakness, index) => (

                            <li key={index}>

                              {weakness}

                            </li>

                          )

                        )}

                      </ul>

                    </section>

                  </div>

                )}



                {activeTab === "qa" && (

                  <div className="tab-content">

                    <section className="result-section">

                      <h3>

                        RoBERTa ASR Classification

                      </h3>



                      {classifications.map(

                        (classification) => (

                          <div

                            className="classification-row"

                            key={

                              classification.requirement_id

                            }

                          >

                            <strong>

                              {

                                classification.requirement_id

                              }

                            </strong>



                            <div className="chips">

                              {classification.quality_attributes.map(

                                (attribute) => (

                                  <span

                                    className="chip"

                                    key={attribute.name}

                                  >

                                    {attribute.name}{" "}

                                    {(

                                      attribute.confidence *

                                      100

                                    ).toFixed(1)}

                                    %

                                  </span>

                                )

                              )}

                            </div>

                          </div>

                        )

                      )}

                    </section>



                    <section className="result-section">

                      <h3>

                        Project Quality Profile

                      </h3>



                      <div className="quality-profile-grid">

                        {Object.entries(

                          qualityProfile

                        ).map(

                          ([attribute, count]) => (

                            <div

                              className="quality-profile-card"

                              key={attribute}

                            >

                              <span>

                                {attribute}

                              </span>



                              <strong>

                                {count}

                              </strong>

                            </div>

                          )

                        )}

                      </div>

                    </section>

                  </div>

                )}



                {activeTab === "alternatives" && (

                  <div className="tab-content">

                    <section className="result-section">

                      <h3>

                        Architecture Ranking

                      </h3>



                      <div className="ranking-list">

                        {evaluations.map(

                          (evaluation) => (

                            <div

                              className="ranking-row"

                              key={evaluation.style}

                            >

                              <div>

                                <span className="rank-number">

                                  #{evaluation.rank}

                                </span>



                                <strong>

                                  {evaluation.style}

                                </strong>



                                {evaluation.is_tied && (

                                  <span className="tie-badge">

                                    Tied

                                  </span>

                                )}

                              </div>



                              <div className="ranking-score">

                                {

                                  evaluation.normalized_score

                                }

                              </div>

                            </div>

                          )

                        )}

                      </div>

                    </section>



                    <section className="result-section">

                      <h3>

                        Rejected Alternatives

                      </h3>



                      {recommendation?.rejected_alternatives

                        ?.length > 0 ? (

                        recommendation.rejected_alternatives.map(

                          (alternative) => (

                            <div

                              className="alternative-card"

                              key={alternative.style}

                            >

                              <div className="alternative-heading">

                                <strong>

                                  {alternative.style}

                                </strong>



                                <span>

                                  Score{" "}

                                  {alternative.score}

                                </span>

                              </div>



                              <p>

                                {alternative.reason}

                              </p>

                            </div>

                          )

                        )

                      ) : (

                        <p>

                          No rejected alternatives were

                          returned.

                        </p>

                      )}

                    </section>

                  </div>

                )}



                {activeTab === "evidence" && (

                  <div className="tab-content">

                    <section className="result-section">

                      <h3>RAG Retrieval</h3>



                      <p className="query-preview">

                        {result?.retrieval?.query}

                      </p>

                    </section>



                    <section className="result-section">

                      <h3>Retrieved Evidence</h3>



                      {evidence.map((item) => (

                        <div

                          className="evidence-card"

                          key={item.knowledge_id}

                        >

                          <div className="evidence-heading">

                            <strong>

                              {item.knowledge_id}

                            </strong>



                            <span>

                              {(

                                item.relevance_score *

                                100

                              ).toFixed(1)}

                              %

                            </span>

                          </div>



                          <h4>

                            {item.title}

                          </h4>



                          <p>

                            {item.content}

                          </p>



                          <div className="chips evidence-chips">

                            {item.quality_attributes?.map(

                              (attribute) => (

                                <span

                                  className="chip"

                                  key={attribute}

                                >

                                  {attribute}

                                </span>

                              )

                            )}

                          </div>

                        </div>

                      ))}

                    </section>

                  </div>

                )}



                {activeTab === "design" && (

                  <div className="tab-content">

                    <section className="result-section">

                      <h3>High-Level Design</h3>



                      <p>

                        {design?.design_rationale}

                      </p>

                    </section>



                    <section className="result-section architecture-diagram-section">

                      <div className="diagram-section-heading">

                        <div>

                          <h3>Visual High-Level Architecture</h3>

                          <p className="diagram-section-description">

                            Generated directly from the validated components and

                            connections returned by the Architecture Decision

                            workflow.

                          </p>

                        </div>



                        <span className="diagram-style-badge">

                          {design?.style}

                        </span>

                      </div>



                      <ArchitectureDiagram

                        components={design?.components || []}

                        connections={design?.connections || []}
                        theme={theme}

                      />

                    </section>



                    <section className="result-section">

                      <h3>

                        Generated Components

                      </h3>



                      <div className="component-grid">

                        {design?.components?.map(

                          (component) => (

                            <div

                              className="component-card"

                              key={

                                component.component_id

                              }

                            >

                              <div className="component-card-heading">

                                <strong>

                                  {component.name}

                                </strong>



                                <span

                                  className={

                                    component.grounding_type ===

                                    "requirement_derived"

                                      ? "grounding-badge requirement-grounded"

                                      : "grounding-badge structural-grounded"

                                  }

                                >

                                  {component.grounding_type ===

                                  "requirement_derived"

                                    ? "Requirement"

                                    : "Structural"}

                                </span>

                              </div>



                              <span className="component-type-label">

                                {

                                  component.component_type

                                }

                              </span>



                              <p>

                                {

                                  component.responsibility

                                }

                              </p>



                              {component

                                .related_requirements

                                ?.length > 0 && (

                                <div className="chips component-links">

                                  {component.related_requirements.map(

                                    (

                                      requirement

                                    ) => (

                                      <span

                                        className="chip"

                                        key={

                                          requirement

                                        }

                                      >

                                        {

                                          requirement

                                        }

                                      </span>

                                    )

                                  )}

                                </div>

                              )}

                            </div>

                          )

                        )}

                      </div>

                    </section>



                    <section className="result-section">

                      <h3>Connections</h3>



                      <div className="connections-list">

                        {design?.connections?.map(

                          (connection, index) => (

                            <div

                              className="connection-row"

                              key={index}

                            >

                              <strong>

                                {

                                  connection.source

                                }

                              </strong>



                              <span>→</span>



                              <strong>

                                {

                                  connection.target

                                }

                              </strong>



                              <small>

                                {

                                  connection.relationship

                                }

                                {connection.protocol_or_mechanism &&

                                  ` · ${connection.protocol_or_mechanism}`}

                              </small>

                            </div>

                          )

                        )}

                      </div>

                    </section>



                    <section className="result-section">

                      <h3>PlantUML</h3>



                      <pre className="plantuml-box">

                        {

                          result?.result

                            ?.plantuml

                        }

                      </pre>

                    </section>

                  </div>

                )}



                <section className="metadata">

                  <span>

                    {

                      result?.metadata

                        ?.classifier_name

                    }

                  </span>



                  <span>

                    {

                      result?.metadata

                        ?.embedding_model

                    }

                  </span>



                  <span>

                    {result?.metadata?.llm_model}

                  </span>



                  <span>

                    {

                      result?.metadata

                        ?.pipeline_version

                    }

                  </span>



                  <span>

                    {

                      result?.metadata

                        ?.execution_time_ms

                    }{" "}

                    ms

                  </span>

                </section>

              </div>

            )}

          </div>

        </section>

          </main>
        </div>
      </div>
    </div>
  );
}

export default ArchitectureDecisionPage;
