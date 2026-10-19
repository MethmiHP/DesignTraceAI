function InfoList({ items, emptyText = 'None recorded.' }) {
  if (!items || items.length === 0) {
    return <p className="adr-muted">{emptyText}</p>
  }

  return (
    <ul className="adr-info-list">
      {items.map((item, index) => (
        <li key={`${item}-${index}`}>
          {item}
        </li>
      ))}
    </ul>
  )
}


const VALID_TRANSITIONS = {
  proposed: ['accepted', 'deprecated'],
  accepted: ['deprecated'],
  superseded: [],
  deprecated: [],
}


function ADRDetails({
  adr,
  onStatusChange,
  updating,
}) {
  if (!adr) {
    return (
      <main className="adr-details-empty">
        Select an ADR to view its details.
      </main>
    )
  }

  const traceability = adr.traceability || {}

  const availableStatuses =
    VALID_TRANSITIONS[adr.status] || []

  const isTerminal =
    adr.status === 'deprecated' ||
    adr.status === 'superseded'

  return (
    <main className="adr-details-panel">
      <div className="adr-details-header">
        <div>
          <div className="adr-title-meta">
            <span className="adr-id-chip">
              {adr.adr_id}
            </span>

            <span
              className={`adr-status adr-status-${adr.status}`}
            >
              {adr.status}
            </span>
          </div>

          <h2>{adr.title}</h2>

          <p>
            Generated using{' '}
            <strong>{adr.generation_method}</strong>
          </p>
        </div>

        <div className="adr-lifecycle-control">
          <span className="adr-lifecycle-label">
            Status
          </span>

          {isTerminal ? (
            <select
                className="adr-status-select"
                value={adr.status}
                disabled
            >
                <option value={adr.status}>
                {adr.status.charAt(0).toUpperCase() +
                adr.status.slice(1)} (Final)
                </option>
            </select>
          ) : (
            <select
              className="adr-status-select"
              value=""
              disabled={updating}
              onChange={(event) => {
                const nextStatus = event.target.value

                if (nextStatus) {
                  onStatusChange(nextStatus)
                }
              }}
            >
              <option value="">
                {updating
                  ? 'Updating...'
                  : `Current: ${adr.status}`}
              </option>

              {availableStatuses.map((status) => (
                <option
                  key={status}
                  value={status}
                >
                  Change to {status}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      <section className="adr-section">
        <h3>Context</h3>
        <p>{adr.context}</p>
      </section>

      <section className="adr-section">
        <h3>Decision</h3>

        <div className="adr-decision-highlight">
          ✓ {adr.decision}
        </div>
      </section>

      <section className="adr-section">
        <h3>Rationale</h3>

        <p>
          {adr.rationale || 'No rationale recorded.'}
        </p>
      </section>

      <div className="adr-two-column">
        <section className="adr-section adr-card">
          <h3>Benefits</h3>
          <InfoList items={adr.benefits} />
        </section>

        <section className="adr-section adr-card">
          <h3>Risks</h3>
          <InfoList items={adr.risks} />
        </section>
      </div>

      <section className="adr-section">
        <h3>Alternatives Considered</h3>
        <InfoList items={adr.alternatives} />
      </section>

      <section className="adr-section">
        <h3>Rejected Alternative Reasons</h3>

        <InfoList
          items={adr.rejected_alternative_reasons}
        />
      </section>

      <section className="adr-section">
        <h3>Trade-offs</h3>
        <InfoList items={adr.trade_offs} />
      </section>

      <section className="adr-section">
        <h3>Consequences</h3>
        <InfoList items={adr.consequences} />
      </section>

      <section className="adr-section">
        <h3>Evidence</h3>
        <InfoList items={adr.evidence} />
      </section>

      <section className="adr-section">
        <h3>Traceability</h3>

        <div className="adr-trace-grid">
          <div>
            <span>Requirements</span>

            <div className="adr-chip-list">
              {(traceability.requirement_ids || []).map(
                (id) => (
                  <span
                    className="adr-trace-chip"
                    key={id}
                  >
                    {id}
                  </span>
                )
              )}

              {(traceability.requirement_ids || [])
                .length === 0 && (
                <span className="adr-muted">
                  None
                </span>
              )}
            </div>
          </div>

          <div>
            <span>Design Elements</span>

            <div className="adr-chip-list">
              {(traceability.design_element_ids || []).map(
                (id) => (
                  <span
                    className="adr-trace-chip"
                    key={id}
                  >
                    {id}
                  </span>
                )
              )}

              {(traceability.design_element_ids || [])
                .length === 0 && (
                <span className="adr-muted">
                  None
                </span>
              )}
            </div>
          </div>

          <div>
            <span>Source Decisions</span>

            <div className="adr-chip-list">
              {(traceability.source_decision_ids || []).map(
                (id) => (
                  <span
                    className="adr-trace-chip"
                    key={id}
                  >
                    {id}
                  </span>
                )
              )}
            </div>
          </div>

          <div>
            <span>Source Modules</span>

            <div className="adr-chip-list">
              {(traceability.source_modules || []).map(
                (source) => (
                  <span
                    className="adr-trace-chip"
                    key={source}
                  >
                    {source}
                  </span>
                )
              )}
            </div>
          </div>
        </div>
      </section>
    </main>
  )
}

export default ADRDetails