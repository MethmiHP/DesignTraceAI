export default function RequirementSummary({ result }) {
  if (!result?.summary) {
    return null;
  }

  const summary = result.summary;

  const issueCount =
    (summary.ambiguous_count || 0) +
    (summary.incomplete_count || 0) +
    (summary.conflict_count || 0) +
    (summary.potentially_missing_count || 0);

  return (
    <section className="analysis-summary-section">
      <div className="analysis-complete-banner">
        <div>
          <span className="analysis-complete-icon">
            ✓
          </span>
        </div>

        <div>
          <h2>Analysis Complete</h2>

          <p>
            Requirements were extracted, classified,
            and evaluated successfully.
          </p>
        </div>
      </div>

      <div className="summary-cards">
        <div className="summary-card">
          <span className="summary-card-label">
            Total
          </span>

          <strong>
            {summary.total_requirements || 0}
          </strong>

          <small>
            Requirements
          </small>
        </div>

        <div className="summary-card">
          <span className="summary-card-label">
            FR
          </span>

          <strong>
            {summary.functional_requirements || 0}
          </strong>

          <small>
            Functional
          </small>
        </div>

        <div className="summary-card">
          <span className="summary-card-label">
            NFR
          </span>

          <strong>
            {summary.non_functional_requirements || 0}
          </strong>

          <small>
            Non-Functional
          </small>
        </div>

        <div className="summary-card">
          <span className="summary-card-label">
            ASR
          </span>

          <strong>
            {summary.asr_count || 0}
          </strong>

          <small>
            Architecturally Significant
          </small>
        </div>

        <div className="summary-card">
          <span className="summary-card-label">
            Issues
          </span>

          <strong>
            {issueCount}
          </strong>

          <small>
            Quality Findings
          </small>
        </div>
      </div>
    </section>
  );
}