function TraceabilityInput({
  jsonInput,
  setJsonInput,
  loading,
  onLoadExample,
  onAnalyze,
}) {
  return (
    <section className="json-input-section">
      <div className="json-input-header">
        <div>
          <p className="section-kicker">
            INPUT
          </p>

          <h2>
            Design Context JSON
          </h2>

          <p className="json-help-text">
            Paste the complete traceability request JSON
            below, or load the saved demo example.
          </p>
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={onLoadExample}
        >
          Load Demo Example
        </button>
      </div>

      <textarea
        className="json-input"
        value={jsonInput}
        onChange={(event) =>
          setJsonInput(event.target.value)
        }
        placeholder="Paste traceability request JSON here..."
        spellCheck="false"
      />

      <div className="json-actions">
        <button
          type="button"
          className="primary-button run-button"
          onClick={onAnalyze}
          disabled={
            loading ||
            !jsonInput.trim()
          }
        >
          {loading
            ? 'Analyzing...'
            : 'Run Live Traceability'}
        </button>
      </div>
    </section>
  )
}

export default TraceabilityInput