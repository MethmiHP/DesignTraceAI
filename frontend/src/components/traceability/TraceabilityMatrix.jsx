function TraceabilityMatrix({
  matrix,
  requirementMap,
  artifactMap,
}) {
  function renderArtifacts(ids, type) {
    if (!ids || ids.length === 0) {
      return (
        <span className="artifact empty">
          —
        </span>
      )
    }

    return (
      <div className="artifact-list">
        {ids.map((id) => {
          const artifact = artifactMap[id]

          let label =
            artifact?.name || id

          if (type === 'api' && artifact) {
            label =
              `${artifact.method} ${artifact.path}`
          }

          return (
            <span
              key={id}
              className={`artifact ${type}`}
            >
              {label}
            </span>
          )
        })}
      </div>
    )
  }

  function getCoverageClass(status) {
    if (status === 'FULLY_COVERED') {
      return 'full'
    }

    if (status === 'PARTIALLY_COVERED') {
      return 'partial'
    }

    return 'none'
  }

  function getCoverageLabel(status) {
    if (status === 'FULLY_COVERED') {
      return 'Fully Covered'
    }

    if (status === 'PARTIALLY_COVERED') {
      return 'Partially Covered'
    }

    return 'Not Covered'
  }

  return (
    <section className="table-wrapper">
      <div className="trace-table-container">
        <table className="trace-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Requirement</th>
              <th>Type</th>
              <th>Architecture</th>
              <th>Database</th>
              <th>API Endpoint</th>
              <th>Component</th>
              <th>Coverage Status</th>
            </tr>
          </thead>

          <tbody>
            {matrix.length === 0 ? (
              <tr>
                <td
                  colSpan="8"
                  className="empty-table-message"
                >
                  Paste JSON and click
                  “Run Live Traceability”, or use
                  “Load Demo Example”.
                </td>
              </tr>
            ) : (
              matrix.map((row) => {
                const requirement =
                  requirementMap[
                    row.requirement_id
                  ]

                return (
                  <tr key={row.requirement_id}>
                    <td className="req-id">
                      {row.requirement_id}
                    </td>

                    <td>
                      {requirement?.statement ||
                        row.requirement_id}
                    </td>

                    <td>
                      <span
                        className={
                          requirement?.requirement_type ===
                          'NFR'
                            ? 'priority medium'
                            : 'priority high'
                        }
                      >
                        {requirement?.requirement_type ||
                          'FR'}
                      </span>
                    </td>

                    <td>
                      {renderArtifacts(
                        row.architecture_links,
                        'architecture',
                      )}
                    </td>

                    <td>
                      {renderArtifacts(
                        row.database_links,
                        'database',
                      )}
                    </td>

                    <td>
                      {renderArtifacts(
                        row.api_links,
                        'api',
                      )}
                    </td>

                    <td>
                      {renderArtifacts(
                        row.component_links,
                        'software',
                      )}
                    </td>

                    <td>
                      <span
                        className={`coverage-status ${getCoverageClass(
                          row.coverage_status,
                        )}`}
                      >
                        ●{' '}
                        {getCoverageLabel(
                          row.coverage_status,
                        )}
                      </span>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>
    </section>
  )
}

export default TraceabilityMatrix