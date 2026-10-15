function TraceabilitySummary({
  totalRequirements,
  fullyCovered,
  partiallyCovered,
  uncovered,
  requirementCoverage,
}) {
  function percentage(value) {
    if (!totalRequirements) {
      return '0%'
    }

    return `${(
      (value / totalRequirements) *
      100
    ).toFixed(1)}%`
  }

  return (
    <section className="summary-grid">
      <div className="summary-card">
        <div className="summary-icon blue">
          ☷
        </div>

        <div>
          <p>Total Requirements</p>
          <h2>{totalRequirements}</h2>
        </div>
      </div>

      <div className="summary-card">
        <div className="summary-icon green">
          ✓
        </div>

        <div>
          <p>Fully Covered</p>

          <div className="summary-value-row">
            <h2>{fullyCovered}</h2>

            <span className="green-text">
              {percentage(fullyCovered)}
            </span>
          </div>
        </div>
      </div>

      <div className="summary-card">
        <div className="summary-icon orange">
          !
        </div>

        <div>
          <p>Partially Covered</p>

          <div className="summary-value-row">
            <h2>{partiallyCovered}</h2>

            <span className="orange-text">
              {percentage(partiallyCovered)}
            </span>
          </div>
        </div>
      </div>

      <div className="summary-card">
        <div className="summary-icon red">
          ?
        </div>

        <div>
          <p>Not Covered</p>

          <div className="summary-value-row">
            <h2>{uncovered}</h2>

            <span className="red-text">
              {percentage(uncovered)}
            </span>
          </div>
        </div>
      </div>

      <div className="summary-card coverage-card">
        <div
          className="coverage-circle"
          style={{
            background: `
              radial-gradient(
                circle,
                var(--panel) 57%,
                transparent 59%
              ),
              conic-gradient(
                var(--green) 0 ${requirementCoverage}%,
                var(--border) ${requirementCoverage}% 100%
              )
            `,
          }}
        >
          <span>
            {requirementCoverage.toFixed(0)}%
          </span>
        </div>

        <div>
          <p>Requirement Coverage</p>

          <h2>
            {requirementCoverage.toFixed(0)}%
          </h2>

          <span className="green-text">
            {requirementCoverage === 100
              ? 'Complete'
              : 'In Progress'}
          </span>
        </div>
      </div>
    </section>
  )
}

export default TraceabilitySummary