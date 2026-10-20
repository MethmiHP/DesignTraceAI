import { useState } from 'react'

const LABELS = {
  requirement_analysis: 'Requirement Analysis',
  architecture_design: 'Architecture Design',
  database_design: 'Database Design',
  api_component_design: 'API & Component Design',
  traceability: 'Traceability',
  quality_evaluation: 'Quality Evaluation',
  adr: 'Architecture Decision Records',
}

function JsonView({ value }) {
  return (
    <pre className="dt2-readable-json">
      {JSON.stringify(value ?? {}, null, 2)}
    </pre>
  )
}

function Table({ columns, rows }) {
  if (!rows?.length) {
    return <p className="dt2-readable-muted">No records available.</p>
  }

  return (
    <div className="dt2-readable-table-wrap">
      <table className="dt2-readable-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key}>{column.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              {columns.map((column) => {
                const value = row[column.key]
                return (
                  <td key={column.key}>
                    {Array.isArray(value)
                      ? value.join(', ')
                      : typeof value === 'object' && value !== null
                        ? JSON.stringify(value)
                        : String(value ?? '—')}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function Section({ title, children }) {
  return (
    <section className="dt2-readable-section">
      <h3>{title}</h3>
      {children}
    </section>
  )
}

function RequirementResults({ data }) {
  return (
    <>
      <Section title="Identified Requirements">
        <Table
          columns={[
            { key: 'id', label: 'ID' },
            { key: 'requirement_text', label: 'Requirement' },
            { key: 'type', label: 'Type' },
            { key: 'priority', label: 'Priority' },
          ]}
          rows={data.requirements}
        />
      </Section>

      <Section title="SRS Summary">
        <p>{data.summary}</p>
        <p>{data.srs?.scope}</p>
      </Section>

      <Section title="Requirement Quality Issues">
        {data.quality_issues?.length
          ? <JsonView value={data.quality_issues} />
          : <p>No issues listed in this mock example.</p>}
      </Section>
    </>
  )
}

function ArchitectureResults({ data }) {
  return (
    <>
      <div className="dt2-readable-metrics">
        <div>
          <small>Architecture Style</small>
          <strong>{data.architecture_style}</strong>
        </div>
        <div>
          <small>Database</small>
          <strong>{data.database_type}</strong>
        </div>
      </div>

      <Section title="Architecture Components">
        <Table
          columns={[
            { key: 'name', label: 'Component' },
            { key: 'responsibility', label: 'Responsibility' },
          ]}
          rows={data.component_details}
        />
      </Section>

      <Section title="Technology Decisions">
        <JsonView value={data.technology_decisions} />
      </Section>

      <Section title="Design Rationale">
        <p>{data.design_rationale}</p>
      </Section>
    </>
  )
}

function DatabaseResults({ data }) {
  return (
    <>
      {data.demo_issue && (
        <div className="dt2-readable-warning">
          Mock demonstration issue: {data.demo_issue}
        </div>
      )}

      <Section title="Database Tables">
        {(data.tables || []).map((table) => (
          <div
            className="dt2-readable-subcard"
            key={table.name}
          >
            <h4>{table.name}</h4>
            <p>Primary key: {table.primary_key}</p>
            <Table
              columns={[
                { key: 'name', label: 'Column' },
                { key: 'type', label: 'Data Type' },
                { key: 'foreign_key', label: 'References' },
              ]}
              rows={table.columns}
            />
          </div>
        ))}
      </Section>

      <Section title="Entity Relationships">
        <Table
          columns={[
            { key: 'from', label: 'From' },
            { key: 'to', label: 'To' },
            { key: 'foreign_key', label: 'Foreign Key' },
            { key: 'cardinality', label: 'Cardinality' },
          ]}
          rows={data.relationships}
        />
      </Section>

      <Section title="Illustrative SQL">
        <pre className="dt2-readable-json">
          {data.sql || 'No SQL provided.'}
        </pre>
      </Section>
    </>
  )
}

function ApiResults({ data }) {
  return (
    <>
      <Section title="Software Components">
        <Table
          columns={[
            { key: 'name', label: 'Component' },
            { key: 'responsibility', label: 'Responsibility' },
            { key: 'requirements', label: 'Requirements' },
          ]}
          rows={data.component_details}
        />
      </Section>

      <Section title="API Endpoints">
        <Table
          columns={[
            { key: 'method', label: 'Method' },
            { key: 'path', label: 'Endpoint' },
            { key: 'component', label: 'Component' },
            { key: 'requirement_id', label: 'Requirement' },
          ]}
          rows={data.endpoints}
        />
      </Section>
    </>
  )
}

function TraceabilityResults({ data }) {
  return (
    <Section title="Requirement Traceability Matrix">
      <Table
        columns={[
          { key: 'requirement_id', label: 'Requirement' },
          { key: 'architecture', label: 'Architecture' },
          { key: 'database', label: 'Database' },
          { key: 'component', label: 'Component' },
          { key: 'endpoint', label: 'Endpoint' },
        ]}
        rows={data.mappings}
      />
    </Section>
  )
}

function QualityResults({ data }) {
  return (
    <>
      <div className="dt2-readable-warning">
        These are illustrative mock scores, not measured
        research results.
      </div>

      <div className="dt2-readable-metrics">
        {Object.entries(data.mock_scores || {}).map(
          ([name, value]) => (
            <div key={name}>
              <small>{name.replaceAll('_', ' ')}</small>
              <strong>{value}%</strong>
            </div>
          )
        )}
      </div>

      <Section title="Evaluation Findings">
        <ul>
          {(data.findings || []).map((finding, index) => (
            <li key={index}>{finding}</li>
          ))}
        </ul>
      </Section>

      <Section title="Recommendations">
        <ul>
          {(data.recommendations || []).map((item, index) => (
            <li key={index}>{item}</li>
          ))}
        </ul>
      </Section>
    </>
  )
}

function AdrResults({ data }) {
  return (
    <Section title="Architecture Decision Records">
      {(data.records || []).map((record) => (
        <div className="dt2-readable-subcard" key={record.id}>
          <h4>{record.id}: {record.title || record.decision}</h4>
          <p><strong>Decision:</strong> {record.decision}</p>
          <p><strong>Status:</strong> {record.status || 'Proposed'}</p>
          <p><strong>Context:</strong> {record.context}</p>
          <p><strong>Rationale:</strong> {record.reason}</p>
          <p>
            <strong>Alternatives:</strong>{' '}
            {(record.alternatives || []).join(', ') || '—'}
          </p>
          <p>
            <strong>Consequences:</strong>{' '}
            {(record.consequences || []).join('; ') || '—'}
          </p>
        </div>
      ))}
    </Section>
  )
}

const VIEWERS = {
  requirement_analysis: RequirementResults,
  architecture_design: ArchitectureResults,
  database_design: DatabaseResults,
  api_component_design: ApiResults,
  traceability: TraceabilityResults,
  quality_evaluation: QualityResults,
  adr: AdrResults,
}

export default function ModuleResultViewer({
  moduleName,
  output,
}) {
  const [showJson, setShowJson] = useState(false)

  // Coordinator outputs are wrapped in an envelope:
  // { project_id, module_name, version, mock, data: {...} }
  const data = output?.data || output || {}
  const Viewer = VIEWERS[moduleName]

  if (!output) {
    return (
      <p className="dt2-readable-muted">
        No Module output available yet.
      </p>
    )
  }

  return (
    <div className="dt2-readable">
      <div className="dt2-readable-heading">
        <div>
          <h3>{LABELS[moduleName] || moduleName}</h3>
          <p>
            {output?.mock === true
              ? 'Simulated PP1 Module output'
              : 'Saved Module output'}
          </p>
        </div>

        <button
          type="button"
          className="dt2-btn"
          onClick={() => setShowJson((previous) => !previous)}
        >
          {showJson ? 'Readable View' : 'Raw JSON'}
        </button>
      </div>

      {showJson ? (
        <JsonView value={output} />
      ) : Viewer ? (
        <Viewer data={data} />
      ) : (
        <JsonView value={output} />
      )}
    </div>
  )
}
