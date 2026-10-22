import './FinalReportViewer.css'

const MODULES = [
  ['requirement_analysis', 'Requirement Analysis'],
  ['architecture_design', 'Architecture Design'],
  ['database_design', 'Database Design'],
  ['api_component_design', 'API & Component Design'],
  ['traceability', 'Traceability'],
  ['quality_evaluation', 'Quality Evaluation'],
  ['adr', 'Architecture Decision Records'],
]

function display(value) {
  if (Array.isArray(value)) return value.join(', ') || '—'
  if (value === null || value === undefined) return '—'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

function ReportTable({ headers, rows }) {
  return (
    <div className="fr-table-scroll">
      <table className="fr-table">
        <thead>
          <tr>
            {headers.map((heading) => (
              <th key={heading}>{heading}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              {row.map((cell, column) => (
                <td key={column}>{display(cell)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function ReportSection({ number, title, children }) {
  return (
    <section className="fr-section">
      <h2>
        <span>{number}</span> {title}
      </h2>
      {children}
    </section>
  )
}

function BulletList({ items }) {
  if (!items?.length) return <p>None recorded.</p>

  return (
    <ul className="fr-list">
      {items.map((item, index) => (
        <li key={index}>{display(item)}</li>
      ))}
    </ul>
  )
}

export default function FinalReportViewer({ response }) {
  const report = response?.report

  if (!report) {
    return <p>Final report is not available yet.</p>
  }

  const artifacts = report.approved_artifacts || {}
  const statuses = report.module_statuses || {}

  const requirements = report.requirements || []
  const requirementData =
    artifacts.requirement_analysis?.data || {}
  const architecture =
    artifacts.architecture_design?.data || {}
  const database =
    artifacts.database_design?.data || {}
  const api =
    artifacts.api_component_design?.data || {}
  const traceability =
    artifacts.traceability?.data || {}
  const quality =
    artifacts.quality_evaluation?.data || {}
  const adr =
    artifacts.adr?.data || {}

  const approvedCount = MODULES.filter(
    ([id]) => statuses[id]?.status === 'APPROVED'
  ).length

  const dbStatus = statuses.database_design || {}

  const generatedDate = report.generated_at
    ? new Date(report.generated_at).toLocaleString()
    : 'Not available'

  const isMock =
    report.execution_mode === 'MOCK_PP1' ||
    Object.values(artifacts).some(
      (artifact) => artifact?.mock === true
    )

  function downloadJson() {
    const blob = new Blob(
      [JSON.stringify(report, null, 2)],
      { type: 'application/json' }
    )

    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download =
      `DesignTraceAI_${report.project_id}_Final_Report.json`
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()

    setTimeout(() => URL.revokeObjectURL(url), 1000)
  }

  function printReport() {
    window.print()
  }

  return (
    <div className="fr-root">
      <div className="fr-actions">
        <button
          type="button"
          className="fr-btn fr-primary"
          onClick={printReport}
        >
          Save as PDF
        </button>

        <button
          type="button"
          className="fr-btn"
          onClick={printReport}
        >
          Print Report
        </button>

        <button
          type="button"
          className="fr-btn"
          onClick={downloadJson}
        >
          Download JSON
        </button>
      </div>

      <article className="fr-document">
        <header className="fr-cover">
          <div className="fr-brand">DESIGNTRACE AI</div>

          <h1>Final Software Design Report</h1>

          <p className="fr-project">
            {report.project_name || report.project_id}
          </p>

          <div className="fr-cover-details">
            <div>
              <span>Project ID</span>
              <strong>{report.project_id}</strong>
            </div>

            <div>
              <span>Generated</span>
              <strong>{generatedDate}</strong>
            </div>

            <div>
              <span>Workflow Status</span>
              <strong>{report.workflow_status}</strong>
            </div>

            <div>
              <span>Execution Mode</span>
              <strong>{report.execution_mode}</strong>
            </div>
          </div>
        </header>

        {isMock && (
          <div className="fr-notice">
            <strong>MOCK DEMONSTRATION</strong>
            <p>
              Module outputs and quality scores are illustrative
              mock data. This report demonstrates Coordinator
              orchestration, review, retry, traceability and
              persistence. It is not a report of independently
              generated or measured software designs.
            </p>
          </div>
        )}

        <ReportSection number="01" title="Executive Summary">
          <p>
            The DesignTrace AI Coordinator processed the
            {` ${report.project_name || 'project'} `}
            through seven software design Modules.
            The workflow status is
            <strong> {report.workflow_status}</strong>.
          </p>

          <div className="fr-metrics">
            <div>
              <span>Approved Modules</span>
              <strong>{approvedCount} / 7</strong>
            </div>

            <div>
              <span>Requirements</span>
              <strong>{requirements.length}</strong>
            </div>

            <div>
              <span>Database Version</span>
              <strong>{dbStatus.version || '—'}</strong>
            </div>

            <div>
              <span>Database Retries</span>
              <strong>{dbStatus.retry_count || 0}</strong>
            </div>
          </div>
        </ReportSection>

        <ReportSection number="02" title="Workflow Module Summary">
          <ReportTable
            headers={[
              'Module',
              'Status',
              'Version',
              'Retries',
            ]}
            rows={MODULES.map(([id, label]) => [
              label,
              statuses[id]?.status || 'NOT RUN',
              statuses[id]?.version ?? '—',
              statuses[id]?.retry_count ?? 0,
            ])}
          />
        </ReportSection>

        <ReportSection number="03" title="Requirement Analysis">
          <p>
            {requirementData.summary ||
              'Requirement analysis results.'}
          </p>

          <ReportTable
            headers={['ID', 'Requirement', 'Type', 'Priority']}
            rows={(
              requirementData.requirements?.length
                ? requirementData.requirements
                : requirements
            ).map((item) => [
              item.requirement_id || item.id,
              item.requirement_text,
              item.type || item.requirement_type,
              item.priority,
            ])}
          />

          <h3>System Scope</h3>
          <p>{requirementData.srs?.scope || 'Not provided.'}</p>
        </ReportSection>

        <ReportSection number="04" title="Architecture Design">
          <p>
            <strong>Architecture Style:</strong>{' '}
            {display(architecture.architecture_style)}
          </p>

          <p>
            <strong>Database:</strong>{' '}
            {display(architecture.database_type)}
          </p>

          <h3>Architecture Components</h3>
          <ReportTable
            headers={['Component', 'Responsibility']}
            rows={(architecture.component_details || []).map(
              (component) => [
                component.name,
                component.responsibility,
              ]
            )}
          />

          <h3>Design Rationale</h3>
          <p>
            {architecture.design_rationale ||
              'Not provided.'}
          </p>
        </ReportSection>

        <ReportSection number="05" title="Database Design">
          <p>
            <strong>Database Technology:</strong>{' '}
            {display(database.database_type)}
          </p>

          <p>
            <strong>Approved Version:</strong>{' '}
            {dbStatus.version || '—'}
          </p>

          <h3>Database Tables</h3>

          {(database.tables || []).map((table) => (
            <div className="fr-subsection" key={table.name}>
              <h4>{table.name}</h4>

              <p>
                Primary Key: {display(table.primary_key)}
              </p>

              <ReportTable
                headers={['Column', 'Type', 'Reference']}
                rows={(table.columns || []).map((column) => [
                  column.name,
                  column.type,
                  column.foreign_key || '—',
                ])}
              />
            </div>
          ))}

          <h3>Entity Relationships</h3>
          <ReportTable
            headers={[
              'From',
              'To',
              'Foreign Key',
              'Cardinality',
            ]}
            rows={(database.relationships || []).map(
              (relationship) => [
                relationship.from,
                relationship.to,
                relationship.foreign_key,
                relationship.cardinality,
              ]
            )}
          />

          <h3>SQL Schema (Illustrative)</h3>
          <pre className="fr-code">
            {database.sql || 'SQL not available.'}
          </pre>
        </ReportSection>

        <ReportSection
          number="06"
          title="API & Component Design"
        >
          <h3>Software Components</h3>
          <ReportTable
            headers={['Component', 'Responsibility', 'Requirements']}
            rows={(api.component_details || []).map(
              (component) => [
                component.name,
                component.responsibility,
                component.requirements,
              ]
            )}
          />

          <h3>API Endpoints</h3>
          <ReportTable
            headers={[
              'Method',
              'Endpoint',
              'Component',
              'Requirement',
            ]}
            rows={(api.endpoints || []).map((endpoint) => [
              endpoint.method,
              endpoint.path,
              endpoint.component,
              endpoint.requirement_id,
            ])}
          />
        </ReportSection>

        <ReportSection number="07" title="Traceability Matrix">
          <ReportTable
            headers={[
              'Requirement',
              'Architecture',
              'Database',
              'Component',
              'Endpoint',
            ]}
            rows={(traceability.mappings || []).map(
              (mapping) => [
                mapping.requirement_id,
                mapping.architecture,
                mapping.database,
                mapping.component,
                mapping.endpoint,
              ]
            )}
          />

          <h3>Unmapped Requirements</h3>
          <BulletList
            items={traceability.unmapped_requirements || []}
          />
        </ReportSection>

        <ReportSection number="08" title="Quality Evaluation">
          <p className="fr-disclaimer">
            The following scores are illustrative mock scores,
            not independently measured research results.
          </p>

          <div className="fr-metrics">
            {Object.entries(
              quality.mock_scores || {}
            ).map(([key, value]) => (
              <div key={key}>
                <span>
                  {key.replaceAll('_', ' ')}
                </span>
                <strong>{value}%</strong>
              </div>
            ))}
          </div>

          <h3>Findings</h3>
          <BulletList items={quality.findings || []} />

          <h3>Recommendations</h3>
          <BulletList items={quality.recommendations || []} />
        </ReportSection>

        <ReportSection
          number="09"
          title="Architecture Decision Records"
        >
          {(adr.records || []).map((record) => (
            <div className="fr-subsection" key={record.id}>
              <h4>
                {record.id} — {record.title || record.decision}
              </h4>

              <p><strong>Status:</strong> {record.status}</p>
              <p><strong>Context:</strong> {record.context}</p>
              <p><strong>Decision:</strong> {record.decision}</p>
              <p><strong>Rationale:</strong> {record.reason}</p>

              <p>
                <strong>Alternatives:</strong>{' '}
                {display(record.alternatives)}
              </p>

              <p>
                <strong>Consequences:</strong>{' '}
                {display(record.consequences)}
              </p>
            </div>
          ))}
        </ReportSection>

        <ReportSection
          number="10"
          title="Human Review & Retry History"
        >
          <ReportTable
            headers={[
              'Module',
              'Approved Version',
              'Retry Count',
              'Feedback',
            ]}
            rows={MODULES.map(([id, label]) => [
              label,
              statuses[id]?.version ?? '—',
              statuses[id]?.retry_count ?? 0,
              (statuses[id]?.human_feedback || []).join('; ') ||
                'No feedback recorded',
            ])}
          />

          {dbStatus.retry_count > 0 && (
            <p className="fr-review-note">
              Database Design was revised following reviewer
              feedback. The approved artifact is version
              {' '}{dbStatus.version}.
            </p>
          )}
        </ReportSection>

        <footer className="fr-document-footer">
          <strong>DesignTrace AI</strong>
          <p>
            Coordinator-generated final report ·
            {` ${report.project_id}`}
          </p>
          {isMock && (
            <p>Mock demonstration — illustrative outputs</p>
          )}
        </footer>
      </article>
    </div>
  )
}
