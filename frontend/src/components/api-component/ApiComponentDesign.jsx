import { useState } from 'react'
import useApiDesign from './useApiDesign'
import GenerationSource from './GenerationSource'
import useTheme from './useTheme'
import DesignContext from './DesignContext'
import { ComponentDesign, Empty, EndpointDetails, Method, Traceability, Validation } from './DesignResults'
import './api-component.css'

const views = [
  ['Context', '▤', 'Design context'],
  ['API Design', '⌘', 'API & Component Design'],
  ['Traceability', '⑂', 'Traceability'],
  ['Validation', '✓', 'Design validation'],
  ['OpenAPI', '▧', 'OpenAPI document'],
]

export default function ApiComponentDesign() {
  const design = useApiDesign()
  const { theme, toggleTheme } = useTheme()
  const { result, submitted, view, setView, busy, error, generate, download } = design
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState('')
  const [tab, setTab] = useState('Overview')
  const operations = result?.api_operations || []
  const keyOf = (item) => `${item.requirement_id}:${item.operation_id}`
  const operation = operations.find((item) => keyOf(item) === selected) || operations[0]
  const filtered = operations.filter((item) => `${item.method} ${item.path} ${item.operation_id} ${item.requirement_id}`.toLowerCase().includes(search.toLowerCase()))
  const groups = Object.groupBy(filtered, (item) => item.element_id)
  const componentIds = new Set(result?.responsibilities.map((item) => item.element_id) || [])
  const responsibility = result?.responsibilities.find((item) => item.requirement_id === operation?.requirement_id && item.element_id === operation?.element_id)
  const element = submitted?.architecture.elements.find((item) => item.element_id === operation?.element_id)
  const requirement = submitted?.functional_requirements.find((item) => item.requirement_id === operation?.requirement_id)
  const warnings = result?.validation.issues.filter((item) => item.severity === 'WARNING') || []

  function navigate(next) { setView(next) }
  function regenerate() { setSearch(''); setSelected(''); generate() }

  return <div className="api-workspace">
    <aside className="workspace-sidebar">
      <a className="brand" href="/" aria-label="DesignTrace AI home"><span className="brand-icon">⌘</span><span>DesignTrace <b>AI</b></span></a>
      <div className="sidebar-caption">DESIGN WORKSPACE</div>
      <nav aria-label="Workspace">{views.map(([name, icon, label]) => <button key={name} disabled={busy} className={view === name || (name === 'API Design' && view === 'Component Design') ? 'nav-item active' : 'nav-item'} onClick={() => navigate(name)}><span aria-hidden="true">{icon}</span>{label}{name === 'Validation' && !!result?.validation.issues.length && <small>{result.validation.issues.length}</small>}</button>)}</nav>
      <div className="sidebar-bottom"><span className="availability-dot" /> API & component module<p>BERT understanding · Context-grounded design</p></div>
    </aside>
    <div className="design-shell">
      <header className="workspace-header"><div><div className="breadcrumb">Design workspace <span>/</span> API & component design</div><h1>API & Component Design</h1><p>Generate and review traceable APIs from requirements, architecture, and data.</p></div><div className="header-actions"><button className="theme-toggle" type="button" onClick={toggleTheme} aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}><span aria-hidden="true">{theme === 'dark' ? '☀' : '☾'}</span>{theme === 'dark' ? 'Light theme' : 'Dark theme'}</button><button disabled={!result || busy} onClick={() => setView('OpenAPI')}>◉ View OpenAPI</button><button disabled={!result || busy} onClick={download}>↓ Export OpenAPI</button></div></header>
      <nav className="workspace-tabs" aria-label="Design sections">{['Context', 'API Design', 'Component Design'].map((name) => <button key={name} disabled={busy} className={view === name ? 'active' : ''} aria-pressed={view === name} onClick={() => setView(name)}>{name === 'Context' ? 'Design Context' : name}</button>)}<span className="project-label">{result?.project_id || design.project || 'No project selected'}</span></nav>
      <div className="design-body">
        <aside className="endpoint-browser"><div className="browser-heading"><h2>API ENDPOINTS</h2><span>{operations.length}</span></div><label className="search-box"><span aria-hidden="true">⌕</span><input aria-label="Search endpoints" placeholder="Search endpoints…" value={search} onChange={(event) => setSearch(event.target.value)} /></label><div className="endpoint-groups">{Object.entries(groups).map(([id, items]) => <section key={id}><h3>⌄ {result.responsibilities.find((item) => item.element_id === id)?.element_name || id}<span>{items.length}</span></h3>{items.map((item) => <button key={keyOf(item)} className={`endpoint-link ${keyOf(operation || {}) === keyOf(item) ? 'selected' : ''}`} onClick={() => { setSelected(keyOf(item)); setView('API Design'); setTab('Overview') }}><Method value={item.method} /><code>{item.path}</code></button>)}</section>)}{!filtered.length && <p className="browser-empty">{operations.length ? 'No endpoints match your search.' : 'Generated endpoints will appear here.'}</p>}</div><div className="totals"><div><small>TOTAL ENDPOINTS</small><strong>{operations.length}</strong></div><div><small>MAPPED COMPONENTS</small><strong>{componentIds.size}</strong></div></div><button className="text-button" disabled={busy} onClick={() => setView('Context')}>← Edit design context</button></aside>
        <main className="design-content" aria-busy={busy}>
          <div role="status" className="sr-only">{busy ? 'Generating API design. This can take a few minutes.' : result ? `Generated ${operations.length} endpoints. Validation ${result.validation.valid ? 'passed' : 'needs attention'}.` : 'Ready for design input.'}</div>
          {busy && <div className="notice loading"><span className="spinner" /> Generating and validating the design…</div>}
          {error && view !== 'Context' && <div className="error" role="alert">{error}<button onClick={() => setView('Context')}>Review inputs</button></div>}
          {!!warnings.length && view !== 'Validation' && <div className="notice warning"><strong>{warnings.length} backend warning{warnings.length > 1 ? 's' : ''}</strong><p>{warnings[0].message}</p><button onClick={() => setView('Validation')}>Review validation →</button></div>}
          {view === 'Context' && <DesignContext design={design} />}
          {view === 'API Design' && (result ? <EndpointDetails operation={operation} result={result} submitted={submitted} tab={tab} setTab={setTab} /> : <Empty title="Your API design starts here" text="Supply your requirements, architecture, and database context. Generated endpoints and their specifications will appear in this workspace."><button className="primary" onClick={() => setView('Context')}>Add design context →</button></Empty>)}
          {view === 'Component Design' && <ComponentDesign result={result} submitted={submitted} />}
          {view === 'Traceability' && <><div className="section-title"><h2>Requirement traceability</h2></div><Traceability result={result} submitted={submitted} /></>}
          {view === 'Validation' && <Validation result={result} />}
          {view === 'OpenAPI' && (result ? <><div className="section-title"><h2>OpenAPI specification</h2><span className="badge">{result.openapi_document?.openapi || 'OpenAPI'}</span></div><p className="muted">Generated from the returned API operations.</p><pre className="openapi-code">{JSON.stringify(result.openapi_document, null, 2)}</pre></> : <Empty title="No OpenAPI document yet" text="Generate a design to view and export its specification." />)}
        </main>
        <aside className="design-inspector"><h2>API Design Details</h2><dl><dt>Component</dt><dd className="component-name">◇ {element?.name || 'No component selected'}</dd><dt>Description</dt><dd>{element?.main_responsibility || 'Component responsibilities are shown after generation.'}</dd><dt>Project</dt><dd>{result?.project_id || design.project || '—'}</dd><dt>Generated by</dt><dd>{operation ? <GenerationSource source={operation.generation_source} /> : 'Not generated'}</dd><dt>Validation</dt><dd>{result ? <span className={`badge ${result.validation.valid ? 'good' : 'warn'}`}>{result.validation.valid ? 'Passed' : 'Needs attention'}{warnings.length ? ` · ${warnings.length} warnings` : ''}</span> : 'Not generated'}</dd></dl><div className="inspector-divider" /><h2>Traceability</h2><div className="inspector-card"><h3>⑂ Functional requirement</h3>{requirement ? <><span className="id-chip">{requirement.requirement_id}</span><p>{requirement.statement}</p></> : <p>No requirement selected.</p>}</div><div className="inspector-card"><h3>◇ System component</h3><p>{responsibility?.element_name || 'Not mapped yet'}</p>{element && <code>{element.element_id}</code>}</div><div className="inspector-card"><h3>⌘ API operation</h3><code>{operation?.operation_id || 'Not generated yet'}</code></div><div className="inspector-note">Designs reflect the supplied context. Review validation issues before using an exported specification.</div></aside>
      </div>
      <footer className="workspace-footer"><button disabled={!result || busy} onClick={() => setView('Validation')}>✓ View validation{result?.validation.issues.length ? ` (${result.validation.issues.length})` : ''}</button><span className="footer-status">{busy ? 'Processing requirements…' : result ? `${operations.length} endpoints · ${componentIds.size} components` : 'Ready to generate'}</span><button className="primary" disabled={busy} type={view === 'Context' ? 'submit' : 'button'} form={view === 'Context' ? 'design-context' : undefined} onClick={view === 'Context' ? undefined : result ? regenerate : () => setView('Context')}>{busy ? 'Generating…' : view === 'Context' ? 'Generate APIs →' : result ? '↻ Regenerate APIs' : 'Add context →'}</button></footer>
    </div>
  </div>
}
