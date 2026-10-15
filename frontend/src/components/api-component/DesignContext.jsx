export default function DesignContext({ design }) {
  const { inputJson, updateInput, formatInput, error, busy, loadExample, generate } = design
  const { gaps, securityChoices, setSecurityChoices, saveSecurity, submitted } = design
  const choose = (field, change) => setSecurityChoices((current) => ({ ...current, [field]: { ...current[field], ...change } }))
  return (
    <form id="design-context" className="context-form" onSubmit={generate}>
      <div className="panel-heading">
        <div><span className="step">01 / INPUT</span><h2>Design context</h2></div>
        <button type="button" onClick={loadExample} disabled={busy}>Load example</button>
      </div>
      {!!gaps.length && <fieldset disabled={busy} className="notice warning">
        <h3>Choose the missing authentication mechanism</h3>
        <p>Authentication is required, but its mechanism was not supplied. Your selection will be saved in the request JSON for each listed requirement before regeneration.</p>
        {gaps.map((gap) => {
          const requirement = submitted.functional_requirements[Number(gap.field.split('.')[1])]
          const choice = securityChoices[gap.field] || {}
          return <div key={gap.field}>
            <label>{requirement.requirement_id}: {requirement.statement}
              <select value={choice.authentication || ''} onChange={(event) => choose(gap.field, { authentication: event.target.value })}>
                <option value="">Choose a mechanism</option>
                <option value="bearer">Bearer token</option>
                <option value="basic">HTTP Basic</option>
                <option value="api_key">API key</option>
              </select>
            </label>
            {choice.authentication === 'api_key' && <>
              <label>API key parameter name<input value={choice.api_key_name || ''} onChange={(event) => choose(gap.field, { api_key_name: event.target.value })} placeholder="X-API-Key" /></label>
              <label>API key location<select value={choice.api_key_location || ''} onChange={(event) => choose(gap.field, { api_key_location: event.target.value })}><option value="">Choose a location</option><option value="header">Header</option><option value="query">Query</option><option value="cookie">Cookie</option></select></label>
            </>}
          </div>
        })}
        <button type="button" className="primary" onClick={saveSecurity}>Save choices and regenerate</button>
      </fieldset>}
      <fieldset disabled={busy}>
        <label htmlFor="design-request">Complete request JSON</label>
        <p id="request-help" className="hint">Paste your project ID, functional requirements, architecture, database, non-functional requirements, and security configuration in one JSON object.</p>
        <textarea id="design-request" className="json-editor" rows={28} required spellCheck={false} autoCapitalize="off" autoCorrect="off" aria-describedby="request-help" value={inputJson} onChange={(event) => updateInput(event.target.value)} placeholder='{"project_id": "banking-001", "functional_requirements": [], "architecture": {"elements": []}, "database": {"entities": []}}' />
        <button type="button" onClick={formatInput} disabled={!inputJson.trim()}>Format JSON</button>
        <p className="hint">Load the security-gap example to test the authentication choice flow. It requires authentication but leaves the mechanism unspecified.</p>
      </fieldset>
      {error && <div className="error" role="alert">{error}</div>}
      <button type="submit" className="primary" disabled={busy}>{busy ? 'Generating design…' : 'Generate API design'}<span aria-hidden="true">→</span></button>
    </form>
  )
}
