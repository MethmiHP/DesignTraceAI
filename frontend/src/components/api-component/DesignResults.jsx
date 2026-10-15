import SecurityDetails from './SecurityDetails'
import GenerationSource from './GenerationSource'

const pretty = (value) => typeof value === 'string' ? value : JSON.stringify(value, null, 2)

export function Method({ value }) {
  return <span className={`method method-${value?.toLowerCase()}`}>{value}</span>
}

export function DataTable({ title, headers, rows, empty = 'None specified in the generated design.' }) {
  return <section className="data-section"><h3>{title}</h3>{rows.length ? <div className="table-scroll"><table><thead><tr>{headers.map((header) => <th key={header}>{header}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={index}>{row.map((cell, i) => <td key={i}>{cell}</td>)}</tr>)}</tbody></table></div> : <p className="table-empty">{empty}</p>}</section>
}

export function Validation({ result }) {
  if (!result) return <Empty title="Validation follows generation" text="Generate a design to see backend validation results and refinement issues." />
  return <div className="validation-view"><div className="section-title"><h2>Design validation</h2><span className={`badge ${result.validation.valid ? 'good' : 'warn'}`}>{result.validation.valid ? 'Passed' : 'Needs attention'}</span></div><p className="muted">Checks returned by the backend for this generated design.</p>{result.validation.issues.length ? result.validation.issues.map((issue, i) => <article className={`issue ${issue.severity === 'ERROR' ? 'issue-error' : ''}`} key={i}><span className="badge warn">{issue.severity}</span><h3>{issue.code.replaceAll('_', ' ')}</h3><p>{issue.message}</p></article>) : <div className="notice good">No validation issues were reported.</div>}</div>
}

export function Empty({ title, text, children }) {
  return <div className="empty-state"><div className="empty-symbol" aria-hidden="true">◇</div><h2>{title}</h2><p>{text}</p>{children}</div>
}

export function Traceability({ result, submitted, requirementId }) {
  const semantics = result?.semantic_extractions.filter((item) => !requirementId || item.requirement_id === requirementId) || []
  if (!semantics.length) return <Empty title="No traceability yet" text="Generate a design to connect requirements to components and API operations." />
  return <div className="trace-list">{semantics.map((semantic, i) => {
    const responsibility = result.responsibilities.find((item) => item.requirement_id === semantic.requirement_id)
    const mappings = result.requirement_to_api_mapping.filter((item) => item.requirement_id === semantic.requirement_id)
    const requirement = submitted?.functional_requirements.find((item) => item.requirement_id === semantic.requirement_id)
    return <article className="trace-card" key={`${semantic.requirement_id}-${i}`}><span className="id-chip">{semantic.requirement_id}</span><h3>{requirement?.statement}</h3><div className="semantic-grid">{[['Actor', semantic.actor], ['Action', semantic.action], ['Resource', semantic.resource]].map(([label, value]) => <div key={label}><small>{label}</small><strong>{value || 'Not identified'}</strong></div>)}</div><p><span className="muted">Component · </span>{responsibility?.element_name || 'Not mapped'}</p><p className="muted">{responsibility?.mapping_reason}</p><div className="mapping-list">{mappings.length ? mappings.map((item, index) => <code key={index}>{item.operation_id}</code>) : <span className="badge warn">No API mapped</span>}</div></article>
  })}</div>
}

export function ComponentDesign({ result, submitted }) {
  if (!result) return <Empty title="Your components, connected" text="Generate a design to see architecture ownership and detailed responsibilities." />
  const elements = submitted?.architecture.elements || []
  return <div><div className="section-title"><h2>Component responsibilities</h2><span className="badge">{elements.length} components</span></div><p className="muted">Supplied architecture with the responsibilities mapped by the backend.</p>{elements.map((element) => {
    const responsibilities = result.responsibilities.filter((item) => item.element_id === element.element_id)
    const operations = result.api_operations.filter((item) => item.element_id === element.element_id)
    return <article className="component-card" key={element.element_id}><div className="section-title"><h3>◇ {element.name}</h3><span className="badge">{element.type}</span></div><code className="muted">{element.element_id}</code><p>{element.main_responsibility}</p>{responsibilities.length ? responsibilities.map((item, index) => <div className="component-responsibility" key={index}><span className="id-chip">{item.requirement_id}</span><p>{item.detailed_responsibility}</p></div>) : <p className="muted">No responsibilities mapped.</p>}<div className="mapping-list">{operations.map((item, i) => <code key={i}>{item.method} {item.path}</code>)}</div></article>
  })}</div>
}

export function EndpointDetails({ operation, result, submitted, tab, setTab }) {
  if (!operation) return <Empty title="No endpoint selected" text="Choose an endpoint from the list. If generation produced none, review the validation issues." />
  const responsibility = result.responsibilities.find((item) => item.requirement_id === operation.requirement_id && item.element_id === operation.element_id)
  const requirement = submitted?.functional_requirements.find((item) => item.requirement_id === operation.requirement_id)
  const spec = result.openapi_document?.paths?.[operation.path]?.[operation.method.toLowerCase()] || {}
  const parameters = spec.parameters || []
  const bodyContentTypes = Object.keys(spec.requestBody?.content || {})
  const headerRows = parameters.filter((item) => item.in === 'header').map((item) => [item.name, pretty(item.schema || {}), item.required ? 'Yes' : 'No', item.description || '—'])
  const securityRequirements = spec.security ?? result.openapi_document?.security ?? []
  const schemeNames = [...new Set(securityRequirements.flatMap((item) => Object.keys(item)))]
  const authRequired = securityRequirements.length > 0 && !securityRequirements.some((item) => Object.keys(item).length === 0)
  for (const name of schemeNames) {
    const scheme = result.openapi_document?.components?.securitySchemes?.[name]
    if (scheme?.type === 'http') headerRows.push(['Authorization', scheme.scheme === 'bearer' ? 'Bearer <token>' : 'Basic <encoded credentials>', authRequired ? 'Yes' : 'Optional', 'Declared authentication credentials.'])
    if (scheme?.type === 'apiKey' && scheme.in === 'header') headerRows.push([scheme.name, 'API key', authRequired ? 'Yes' : 'Optional', 'Declared API key authentication.'])
  }
  if (bodyContentTypes.length) {
    headerRows.push(['Content-Type', bodyContentTypes.join(' / '), spec.requestBody.required ? 'Yes' : 'When sending a body', 'Media type of the request body.'])
  }
  const fields = (schema) => Object.entries(schema || {}).map(([name, type]) => [<code>{name}</code>, <code>{pretty(type)}</code>])
  const parameterRows = (location) => parameters.filter((item) => item.in === location).map((item) => [<code>{item.name}</code>, pretty(item.schema || {}), item.required ? 'Yes' : 'No', item.description || '—'])
  return <>
    <article className="endpoint-card"><div className="endpoint-heading"><Method value={operation.method} /><h2><code>{operation.path}</code></h2><GenerationSource source={operation.generation_source} /></div><p>{responsibility?.detailed_responsibility || operation.operation_id}</p><div className="endpoint-origin"><p><span>Derived from:</span> <span className="id-chip">{operation.requirement_id}</span> {requirement?.statement}</p><p><span>Owned by:</span> ◇ {responsibility?.element_name || operation.element_id}</p></div><div className="operation-id"><span>Operation ID</span><code>{operation.operation_id}</code></div></article>
    <nav className="detail-tabs" aria-label="Endpoint details">{['Overview', 'Request', 'Response', 'Errors', 'Security', 'Traceability'].map((name) => <button key={name} aria-pressed={tab === name} className={tab === name ? 'active' : ''} onClick={() => setTab(name)}>{name}</button>)}</nav>
    {tab === 'Overview' && <><DataTable title="Path parameters" headers={['Parameter', 'Schema', 'Required', 'Description']} rows={parameterRows('path')} empty="This endpoint has no path placeholders." /><DataTable title="Query parameters" headers={['Parameter', 'Schema', 'Required', 'Description']} rows={parameterRows('query')} empty="No query filters are defined for this operation. Body fields appear in the Request tab." /><DataTable title="Request headers" headers={['Header', 'Schema', 'Required', 'Description']} rows={headerRows} empty="No request headers are declared for this operation." /><DataTable title="Responses" headers={['Status code', 'Content type', 'Description']} rows={Object.entries(spec.responses || {}).map(([code, response]) => [<span className={`status-code ${code.startsWith('2') ? 'good' : 'warn'}`}>{code}</span>, Object.keys(response.content || {}).join(', ') || 'Not specified', response.description])} /></>}
    {tab === 'Request' && <><DataTable title="Request headers" headers={['Header', 'Type / value', 'Required', 'Description']} rows={headerRows} /><DataTable title="Request fields" headers={['Field', 'Type / value']} rows={fields(operation.request_schema)} /></>}
    {tab === 'Response' && <DataTable title="Response fields" headers={['Field', 'Type / value']} rows={fields(operation.response_schema)} />}
    {tab === 'Errors' && <DataTable title="Error responses" headers={['Status', 'Description']} rows={Object.entries(operation.error_responses || {})} />}
    {tab === 'Security' && <SecurityDetails operation={operation} spec={spec} document={result.openapi_document} />}
    {tab === 'Traceability' && <Traceability result={result} submitted={submitted} requirementId={operation.requirement_id} />}
  </>
}
