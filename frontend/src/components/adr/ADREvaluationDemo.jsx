import { useState } from 'react'
import { generateADRs } from '../../services/adrService'


const SIGNIFICANT_SAMPLE = {
  project_id: 'BANKING-DESIGN-001',
  decisions: [
    {
      decision_id: 'DEC-ARCH-001',
      project_id: 'BANKING-DESIGN-001',
      source_module: 'architecture_decision',
      title: 'Adopt Microservices Architecture',
      decision:
        'Use a microservices architecture for the system.',
      context:
        'The system must support independently deployable services, high scalability and fault isolation across major business capabilities.',
      rationale:
        'Microservices provide independent scaling and deployment boundaries for major business functions.',
      alternatives: [
        'Layered Architecture',
        'Modular Monolith',
        'Microservices',
      ],
      rejected_alternative_reasons: [
        'Layered architecture provides limited independent scalability.',
        'Modular monolith provides less deployment independence.',
      ],
      decision_criteria: [
        'Scalability',
        'Maintainability',
        'Reliability',
      ],
      benefits: [
        'Independent service deployment',
        'Independent scalability',
        'Fault isolation',
      ],
      risks: [
        'Higher operational complexity',
        'Distributed communication overhead',
      ],
      consequences: [
        'The system will be divided into independently deployable services.',
      ],
      trade_offs: [
        'Improved scalability at the cost of greater operational complexity.',
      ],
      requirement_ids: [
        'NFR-001',
        'NFR-002',
      ],
      design_element_ids: [
        'ARCH-SERVICE-001',
        'ARCH-SERVICE-002',
      ],
      evidence: [
        'Scalability and fault isolation are important architecture requirements.',
      ],
      confidence: 0.95,
    },

    {
      decision_id: 'DEC-DB-001',
      project_id: 'BANKING-DESIGN-001',
      source_module: 'database_design',
      title: 'Use Read Replicas for Reporting Workloads',
      decision:
        'Introduce database read replicas for high-volume reporting queries.',
      context:
        'Reporting queries are expected to create heavy read load and may interfere with transactional writes on the primary database.',
      rationale:
        'Read replicas separate reporting load from transactional write operations.',
      alternatives: [
        'Primary database only',
        'Read replicas',
      ],
      rejected_alternative_reasons: [
        'Using only the primary database may degrade transaction performance.',
      ],
      decision_criteria: [
        'Performance',
        'Scalability',
        'Availability',
      ],
      benefits: [
        'Reduced load on primary database',
        'Improved read scalability',
      ],
      risks: [
        'Replication lag may produce slightly stale reports.',
      ],
      consequences: [
        'Reporting queries will be routed to replicas.',
      ],
      trade_offs: [
        'Better read performance with possible replication delay.',
      ],
      requirement_ids: [
        'NFR-003',
      ],
      design_element_ids: [
        'DB-PRIMARY-001',
        'DB-REPLICA-001',
      ],
      evidence: [
        'Reporting workload is read-heavy and expected to grow.',
      ],
      confidence: 0.92,
    },

    {
      decision_id: 'DEC-API-001',
      project_id: 'BANKING-DESIGN-001',
      source_module: 'api_component_design',
      title: 'Require Idempotency for Payment Requests',
      decision:
        'Require idempotency keys when creating payment transactions.',
      context:
        'Clients may retry requests after network failures, which could otherwise create duplicate payments.',
      rationale:
        'Idempotency prevents duplicate payment processing during retries.',
      alternatives: [
        'Allow unrestricted retries',
        'Use idempotency keys',
      ],
      rejected_alternative_reasons: [
        'Unrestricted retries can create duplicate transactions.',
      ],
      decision_criteria: [
        'Reliability',
        'Security',
      ],
      benefits: [
        'Prevents duplicate payments',
        'Safer retry behaviour',
      ],
      risks: [
        'Requires additional request state management.',
      ],
      consequences: [
        'Clients must provide an idempotency key for payment creation.',
      ],
      trade_offs: [
        'Improved correctness with additional storage and validation logic.',
      ],
      requirement_ids: [
        'FR-021',
        'NFR-004',
      ],
      design_element_ids: [
        'API-PAYMENT-POST-001',
      ],
      evidence: [
        'Payment creation must remain correct under network retries.',
      ],
      confidence: 0.96,
    },

    {
      decision_id: 'DEC-QUAL-001',
      project_id: 'BANKING-DESIGN-001',
      source_module: 'quality_evaluation',
      title: 'Introduce Automatic Failover',
      decision:
        'Use automatic failover for critical production services.',
      context:
        'The quality evaluation identified a single active instance as a major availability weakness.',
      rationale:
        'Automatic failover reduces recovery time when the active instance becomes unavailable.',
      alternatives: [
        'Manual recovery',
        'Automatic failover',
      ],
      rejected_alternative_reasons: [
        'Manual recovery does not satisfy the required availability target.',
      ],
      decision_criteria: [
        'Availability',
        'Reliability',
      ],
      benefits: [
        'Reduced downtime',
        'Faster service recovery',
      ],
      risks: [
        'Requires health monitoring and coordination logic.',
      ],
      consequences: [
        'A standby instance must be maintained and monitored.',
      ],
      trade_offs: [
        'Higher availability with increased infrastructure complexity.',
      ],
      requirement_ids: [
        'NFR-005',
      ],
      design_element_ids: [
        'QUAL-FAILOVER-001',
      ],
      evidence: [
        'Availability evaluation identified failover as a required improvement.',
      ],
      confidence: 0.94,
    },
  ],
}


const MINOR_SAMPLE = {
  project_id: 'BANKING-DESIGN-002',
  decisions: [
    {
      decision_id: 'DEC-API-MINOR-001',
      project_id: 'BANKING-DESIGN-002',
      source_module: 'api_component_design',
      title: 'Rename Internal Handler File',
      decision:
        'Rename one internal handler file to match the repository naming convention.',
      context:
        'The filename is inconsistent with nearby source files, but runtime behaviour is unchanged.',
      rationale:
        'Improve code organisation.',
      alternatives: [
        'Keep current filename',
        'Rename file',
      ],
      rejected_alternative_reasons: [],
      decision_criteria: [],
      benefits: [
        'More consistent naming',
      ],
      risks: [],
      consequences: [
        'No runtime behaviour changes.',
      ],
      trade_offs: [],
      requirement_ids: [],
      design_element_ids: [
        'API-HANDLER-009',
      ],
      evidence: [],
      confidence: 0.9,
    },
  ],
}


function ADREvaluationDemo({ onGenerated }) {
  const [jsonInput, setJsonInput] = useState(
    JSON.stringify(
      SIGNIFICANT_SAMPLE,
      null,
      2
    )
  )

  const [response, setResponse] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')


  function loadSignificantSample() {
    setJsonInput(
      JSON.stringify(
        SIGNIFICANT_SAMPLE,
        null,
        2
      )
    )

    setResponse(null)
    setError('')
  }


  function loadMinorSample() {
    setJsonInput(
      JSON.stringify(
        MINOR_SAMPLE,
        null,
        2
      )
    )

    setResponse(null)
    setError('')
  }


  async function handleSubmit() {
    try {
      setLoading(true)
      setError('')
      setResponse(null)

      const payload = JSON.parse(
        jsonInput
      )

      /*
       * Avoid duplicate-decision conflicts during repeated viva tests.
       * Each submitted decision receives a temporary unique ID.
       */
      const timestamp = Date.now()

      payload.decisions = (
        payload.decisions || []
      ).map((decision, index) => ({
        ...decision,

        decision_id:
          `${decision.decision_id}-${timestamp}-${index + 1}`,
      }))

      const result =
        await generateADRs(payload)

      setResponse(result)

      if (
        result.generated_adr_count > 0 &&
        onGenerated
      ) {
        onGenerated(result.project_id)
      }
    } catch (err) {
      if (err instanceof SyntaxError) {
        setError(
          'Invalid JSON. Please check the input format.'
        )
      } else {
        setError(
          err.message ||
            'Unable to process ADR input.'
        )
      }
    } finally {
      setLoading(false)
    }
  }


  return (
    <div className="adr-demo">

      <div className="adr-demo-heading">

        <div>
          <h2>
            Upstream Decision Preview
          </h2>

          <p>
            Temporary integration view for testing
            structured decisions received from
            upstream DesignTrace modules.
          </p>
        </div>


        <div className="adr-demo-samples">

          <button
            type="button"
            onClick={loadSignificantSample}
          >
            Load Multi-Module Example
          </button>

          <button
            type="button"
            onClick={loadMinorSample}
          >
            Load Minor Example
          </button>

        </div>
      </div>


      <div className="adr-demo-grid">

        {/* INPUT */}
        <section className="adr-demo-panel">

          <div className="adr-demo-panel-title">

            <span>1</span>

            <div>
              <h3>
                Coordinator Input
              </h3>

              <p>
                Structured JSON representing
                decisions received from upstream
                modules.
              </p>
            </div>

          </div>


          <div className="adr-json-wrapper">

            <div className="adr-json-toolbar">

              <span>
                JSON Input
              </span>

              <span>
                POST /api/adr/generate
              </span>

            </div>


            <textarea
              className="adr-json-input"
              value={jsonInput}
              onChange={(event) =>
                setJsonInput(
                  event.target.value
                )
              }
              spellCheck="false"
            />

          </div>


          <button
            type="button"
            className="adr-demo-submit"
            onClick={handleSubmit}
            disabled={loading}
          >
            {loading
              ? 'Processing Decisions...'
              : 'Process Upstream Decisions →'}
          </button>

        </section>


        {/* OUTPUT */}
        <section className="adr-demo-panel">

          <div className="adr-demo-panel-title">

            <span>2</span>

            <div>
              <h3>
                ADR Processing Result
              </h3>

              <p>
                Significance classification and
                generated ADR records.
              </p>
            </div>

          </div>


          {error && (
            <div className="adr-error">
              {error}
            </div>
          )}


          {!response && !loading && (
            <div className="adr-demo-placeholder">

              <div>
                ◇
              </div>

              <strong>
                Waiting for upstream decisions
              </strong>

              <p>
                Load an example or paste coordinator
                JSON and process the decisions.
              </p>

            </div>
          )}


          {loading && (
            <div className="adr-demo-placeholder">

              <strong>
                Processing decisions...
              </strong>

              <p>
                Running significance detection and
                ADR generation.
              </p>

            </div>
          )}


          {response && (
            <div className="adr-demo-result">

              {/* SUMMARY */}
              <div className="adr-result-summary">

                <div>
                  <span>
                    Decisions Received
                  </span>

                  <strong>
                    {response.results?.length || 0}
                  </strong>
                </div>


                <div>
                  <span>
                    ADRs Generated
                  </span>

                  <strong className="adr-significant">
                    {response.generated_adr_count}
                  </strong>
                </div>


                <div>
                  <span>
                    Decisions Skipped
                  </span>

                  <strong>
                    {response.skipped_decision_count}
                  </strong>
                </div>

              </div>


              {/* EACH DECISION */}
              <div className="adr-result-list">

                {response.results?.map(
                  (item) => (
                    <div
                      className="adr-result-card"
                      key={
                        item.decision.decision_id
                      }
                    >

                      <div className="adr-result-card-header">

                        <div>

                          <span className="adr-source-label">
                            {
                              item.decision
                                .source_module
                            }
                          </span>

                          <h3>
                            {
                              item.decision
                                .title
                            }
                          </h3>

                        </div>


                        <div className="adr-result-classification">

                          <strong
                            className={
                              item.significance
                                ?.significant
                                ? 'adr-significant'
                                : 'adr-not-significant'
                            }
                          >
                            {item.significance
                              ?.significant
                              ? '✓ Significant'
                              : '✕ Not Significant'}
                          </strong>

                          <span>
                            {(
                              (item.significance
                                ?.score || 0) * 100
                            ).toFixed(2)}
                            %
                          </span>

                        </div>

                      </div>


                      <div className="adr-demo-reason">
                        {
                          item.significance
                            ?.reasons?.[0]
                        }
                      </div>


                      {item.adr ? (

                        <div className="adr-generated-preview">

                          <div className="adr-demo-generated">
                            ADR GENERATED
                          </div>

                          <div className="adr-output-meta">

                            <span>
                              {item.adr.adr_id}
                            </span>

                            <span>
                              {item.adr.status}
                            </span>

                            <span>
                              {
                                item.adr
                                  .generation_method
                              }
                            </span>

                          </div>


                          <div className="adr-output-section">

                            <h4>
                              Decision
                            </h4>

                            <div className="adr-decision-highlight">
                              ✓ {item.adr.decision}
                            </div>

                          </div>


                          <div className="adr-output-section">

                            <h4>
                              Rationale
                            </h4>

                            <p>
                              {item.adr.rationale}
                            </p>

                          </div>


                          <div className="adr-output-columns">

                            <div>
                              <h4>
                                Benefits
                              </h4>

                              {item.adr.benefits
                                ?.length ? (
                                <ul>
                                  {
                                    item.adr
                                      .benefits
                                      .map(
                                        (
                                          benefit
                                        ) => (
                                          <li
                                            key={
                                              benefit
                                            }
                                          >
                                            {
                                              benefit
                                            }
                                          </li>
                                        )
                                      )
                                  }
                                </ul>
                              ) : (
                                <p>
                                  None recorded.
                                </p>
                              )}
                            </div>


                            <div>
                              <h4>
                                Risks
                              </h4>

                              {item.adr.risks
                                ?.length ? (
                                <ul>
                                  {
                                    item.adr
                                      .risks
                                      .map(
                                        (
                                          risk
                                        ) => (
                                          <li
                                            key={
                                              risk
                                            }
                                          >
                                            {
                                              risk
                                            }
                                          </li>
                                        )
                                      )
                                  }
                                </ul>
                              ) : (
                                <p>
                                  None recorded.
                                </p>
                              )}

                            </div>
                          </div>

                        </div>

                      ) : (

                        <div className="adr-skipped-result">

                          <strong>
                            ADR generation skipped
                          </strong>

                          <p>
                            This decision was not
                            considered architecturally
                            significant enough to
                            require an ADR.
                          </p>

                        </div>

                      )}

                    </div>
                  )
                )}

              </div>

            </div>
          )}

        </section>

      </div>
    </div>
  )
}


export default ADREvaluationDemo