import { useState } from 'react'
import useQualityEvaluation from './useQualityEvaluation'
import './quality-evaluation.css'

const percent = (value) => value == null ? 'N/A' : `${value}%`
const levels = ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
const ranking = { CRITICAL: 4, HIGH: 3, MEDIUM: 2, LOW: 1 }
function Badge({ value }) { return <span className={`qe-badge ${value.toLowerCase()}`}>{value}</span> }
function Panel({ title, subtitle, children, id, extra }) {
  return <section className="qe-panel" id={id}><div className="qe-panel-heading"><div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div>{extra}</div>{children}</section>
}
function Empty({ children }) { return <p className="qe-empty">{children}</p> }

export default function QualityEvaluation() {
  const app = useQualityEvaluation()
  const { result, history, busy, editor, setEditor, theme } = app
  const [filter, setFilter] = useState('ALL')
  const metrics = result?.metrics
  const findings = result?.findings || []
  const visible = findings.filter((item) => filter === 'ALL' || item.severity === filter)
  const urgent = findings.filter((item) => ['HIGH', 'CRITICAL'].includes(item.severity)).length
  const recommendations = [...findings].sort((a, b) => ranking[b.severity] - ranking[a.severity])
  return <div className="qe-app" data-theme={theme}>
    <aside className="qe-sidebar">
      <a className="qe-brand" href="#overview"><span className="qe-logo">◇</span>DesignTrace <b>AI</b></a>
      <div className="qe-project"><small>CURRENT PROJECT</small><strong>{result?.project_id || 'No evaluation yet'}</strong></div>
      <div className="qe-nav-label">DESIGN WORKSPACE</div>
      <nav aria-label="Quality evaluation"><a className="active" href="#overview">◈ <span>Quality Evaluation</span></a><button onClick={() => setEditor(true)}>▤ <span>Evaluation input</span></button><a href="#categories">▦ <span>NFR categories</span></a><a href="#issues">⚑ <span>Detected issues</span></a><a href="#recommendations">◇ <span>Recommendations</span></a><a href="#history">◷ <span>Evaluation history</span></a></nav>
      <div className="qe-sidebar-bottom"><div className="qe-about"><strong>ABOUT EVALUATION</strong><p>Results reflect applicable quality rules and the supplied design evidence. Skipped checks remain visible for review.</p></div><div className="qe-module"><span>QE</span><div>Quality workspace<small>DesignTrace AI</small></div></div><button className="qe-theme" role="switch" aria-checked={theme === 'light'} aria-label="Light theme" onClick={app.toggleTheme}><span>{theme === 'dark' ? '☾ Dark theme' : '☀ Light theme'}</span><span className="qe-switch"><i /></span></button></div>
    </aside>
    <main className="qe-main" id="overview">
      <header className="qe-header"><div><div className="qe-eyebrow">DESIGN ASSURANCE / OVERVIEW</div><h1>Quality Evaluation</h1><p>Continuous architectural and security quality assessment.</p></div><button className="qe-primary" onClick={() => setEditor(true)} disabled={busy}>＋ New evaluation</button></header>
      {editor && <Panel title="Evaluation input" subtitle="Paste the complete coordinator payload to evaluate your design." extra={<button onClick={() => setEditor(false)} disabled={busy} aria-label="Close input">×</button>}>
        <form onSubmit={app.evaluate}><label htmlFor="quality-json">Request JSON</label><textarea id="quality-json" required spellCheck={false} value={app.input} disabled={busy} onChange={(event) => app.setInput(event.target.value)} placeholder='{"project_id": "banking-001", "architecture": {}, "database": {}, "api_component_design": {}}' rows={15} />{app.error && <p className="qe-error" role="alert">{app.error}</p>}<div className="qe-form-actions"><button type="button" onClick={app.loadExample} disabled={busy}>Load example</button><span role="status">{busy ? 'Evaluating design…' : 'Example: banking design with security and scalability gaps.'}</span><button className="qe-primary" disabled={busy}>{busy ? 'Evaluating…' : 'Run evaluation →'}</button></div></form>
      </Panel>}
      <div className="qe-stats">
        <article><small>QUALITY PASS RATE</small><strong>{result ? percent(metrics.quality_pass_percentage) : '—'}</strong><p className="qe-purple">{result ? `${metrics.passed_rules} / ${metrics.total_applicable_rules} applicable rules passed` : 'Awaiting evaluation'}</p></article>
        <article><small>NFR COVERAGE</small><strong>{result ? percent(metrics.nfr_coverage_percentage) : '—'}</strong><p className="qe-blue">{result ? `${metrics.evaluated_nfrs} / ${metrics.applicable_nfrs} applicable NFRs evaluated` : 'Requirements evaluated'}</p></article>
        <article><small>IMMEDIATE ATTENTION</small><strong>{result ? urgent : '—'}</strong><p className="qe-red">High & critical findings</p></article>
        <article><small>TOTAL DETECTED ISSUES</small><strong>{result ? findings.length : '—'}</strong><p className="qe-amber">{result ? `${metrics.skipped_rules} rule(s) skipped` : 'Across all categories'}</p></article>
      </div>
      {!result && <div className="qe-welcome"><span>◇</span><div><h2>A clear view of your design quality</h2><p>Evaluate your requirements and design artifacts to uncover gaps and review actionable findings.</p></div><button onClick={() => { app.loadExample(); setEditor(true) }}>Try the example →</button></div>}
      <div className="qe-grid"><div className="qe-primary-column">
        <Panel id="categories" title="NFR Category Results" subtitle="Pass rates across applicable design quality rules" extra={<span className="qe-info" title="Passed rules divided by all applicable rules, including skipped rules.">ⓘ</span>}>
          <div className="qe-table-scroll"><table><thead><tr><th>Category</th><th>Satisfaction progress</th><th>Passed</th><th>Skipped</th></tr></thead><tbody>{metrics?.category_summaries.map((item) => <tr key={item.category}><td><div className="qe-category"><span>◇</span><div>{item.category}<small>{item.passed_rules} / {item.applicable_rules} rules passed</small></div></div></td><td><div className="qe-progress"><progress aria-label={`${item.category} pass rate`} max="100" value={item.pass_percentage ?? 0} /><span>{percent(item.pass_percentage)}</span></div></td><td>{item.passed_rules}</td><td>{item.skipped_rules}</td></tr>)}</tbody></table></div>{!result && <Empty>Category results will appear after your first evaluation.</Empty>}
        </Panel>
        <Panel id="issues" title="Detected Issues" extra={<span className="qe-count">{findings.length}</span>}>
          <div className="qe-filters" aria-label="Filter findings by severity">{levels.map((level) => <button aria-pressed={filter === level} className={filter === level ? 'selected' : ''} onClick={() => setFilter(level)} key={level}>{level === 'ALL' ? 'All' : level.toLowerCase()} ({level === 'ALL' ? findings.length : findings.filter((item) => item.severity === level).length})</button>)}</div>
          <div className="qe-table-scroll"><table><thead><tr><th>Issue details</th><th>Category</th><th>Severity</th><th>Rule ID</th></tr></thead><tbody>{visible.map((item) => <tr key={item.finding_id}><td><details><summary>{item.rationale}</summary><div className="qe-evidence"><strong>Evidence</strong>{item.evidence.map((e, i) => <p key={i}>{e}</p>)}<p>NFRs: {item.affected_nfr_ids.join(', ') || 'None linked'}</p><p>{item.recommendation}</p></div></details></td><td>{item.quality_attribute}</td><td><Badge value={item.severity} /></td><td><code>{item.rule_id}</code></td></tr>)}</tbody></table></div>{!visible.length && <Empty>{result ? 'No findings match this filter.' : 'Run an evaluation to review detected issues.'}</Empty>}
        </Panel>
        {!!result?.finding_groups?.length && <Panel title="Related Findings">{result.finding_groups.map((group) => <div className="qe-group" key={group.group_id}><Badge value={group.severity} /><h3>{group.title}</h3><p>{group.summary}</p><small>{group.rule_ids.join(' · ')}</small>{group.recommendations.map((text, i) => <p key={i}>{text}</p>)}</div>)}</Panel>}
        <Panel id="history" title="Evaluation History" subtitle="Runs from this session · select a run to review its results">
          <div className="qe-table-scroll"><table><thead><tr><th>Run ID</th><th>Date & time</th><th>Pass rate</th><th>NFR coverage</th><th>Issues</th></tr></thead><tbody>{history.map((run) => <tr key={run.evaluation_id}><td><button className="qe-text-button" onClick={() => { app.setResult(run); setFilter('ALL') }}>{run.evaluation_id}</button><small>{run.project_id}</small></td><td>{new Date(run.generated_at).toLocaleString()}</td><td>{percent(run.metrics.quality_pass_percentage)}</td><td>{percent(run.metrics.nfr_coverage_percentage)}</td><td>{run.findings.length}</td></tr>)}</tbody></table></div>{!history.length && <Empty>Your completed evaluations will appear here.</Empty>}
        </Panel>
      </div><aside className="qe-secondary-column">
        <Panel title="Understanding the Results"><div className="qe-legend"><p><span className="qe-dot pass" /><strong>Pass</strong> Rule requirements satisfied</p><p><span className="qe-dot fail" /><strong>Fail</strong> A design gap was detected</p><p><span className="qe-dot skip" /><strong>Skipped</strong> Check was not completed</p><p><span className="qe-dot na" /><strong>N/A</strong> No applicable rules or NFRs</p></div></Panel>
        <Panel title="✧ Quality Summary"><p className="qe-summary">{result?.summary || 'A summary of the evaluated design will appear here. Start with your coordinator JSON or load the example.'}</p></Panel>
        <Panel id="recommendations" title="Key Recommendations">{recommendations.length ? recommendations.map((item) => <article className="qe-recommendation" key={item.finding_id}><Badge value={item.severity} /><p>{item.recommendation}</p><code>Rule: {item.rule_id}</code></article>) : <Empty>{result ? 'No recommendations were returned.' : 'Recommendations will be grounded in your evaluation findings.'}</Empty>}</Panel>
        {!!result?.rule_results.filter((item) => item.status === 'SKIPPED').length && <Panel title="Checks Needing Review">{result.rule_results.filter((item) => item.status === 'SKIPPED').map((item) => <div className="qe-group" key={item.rule_id}><code>{item.rule_id}</code><p>{item.rationale}</p></div>)}</Panel>}
      </aside></div>
      <footer className="qe-footer"><button onClick={() => setEditor(true)}>← Edit evaluation input</button><span>{result ? `Run ${result.evaluation_id}` : 'Ready to evaluate'}</span><button className="qe-primary" disabled={!result || busy} onClick={app.exportResult}>Export report ↓</button></footer>
    </main>
  </div>
}
