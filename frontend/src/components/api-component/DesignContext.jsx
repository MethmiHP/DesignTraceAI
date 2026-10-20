export default function DesignContext({ design }) {
  const { inputJson, updateInput, formatInput, error, busy, loadExample, generate } = design
  const { gaps, securityChoices, setSecurityChoices, saveSecurity } = design
  const choice = securityChoices
  const choose = (change) => setSecurityChoices((current) => ({ ...current, ...change }))
  return (
    <form id="design-context" className="context-form" onSubmit={generate}>
      <div className="panel-heading">
        <div><span className="step">01 / INPUT</span><h2>Design context</h2></div>
        <button type="button" onClick={loadExample} disabled={busy}>Load example</button>
      </div>
      {!!gaps.length && <fieldset disabled={busy} className="notice warning">
        <h3>Choose the missing authentication mechanism</h3>
        <p>Choose one shared mechanism for the missing authentication configuration. Existing explicit requirement policies are preserved.</p>
        <label>Authentication mechanism
          <select value={choice.authentication || ''} onChange={(event) => setSecurityChoices({ authentication: event.target.value })}>
            <option value="">Choose a mechanism</option>
            <option value="bearer">Bearer Token</option>
            <option value="oauth2">OAuth 2.0</option>
            <option value="openid_connect">OpenID Connect</option>
            <option value="api_key">API Key</option>
            <option value="basic">HTTP Basic</option>
            <option value="mutual_tls">Mutual TLS (mTLS)</option>
            <option value="custom">Custom / Other</option>
            <option value="unspecified">Not specified yet</option>
          </select>
        </label>
        {choice.authentication === 'api_key' && <>
          <label>API key parameter name<input value={choice.api_key_name || ''} onChange={(event) => choose({ api_key_name: event.target.value })} placeholder="X-API-Key" /></label>
          <label>API key location<select value={choice.api_key_location || ''} onChange={(event) => choose({ api_key_location: event.target.value })}><option value="">Choose a location</option><option value="header">Header</option><option value="query">Query</option><option value="cookie">Cookie</option></select></label>
        </>}
        {choice.authentication === 'oauth2' && <label>OAuth flows (OpenAPI JSON)<textarea rows={5} value={choice.oauth_flows_json || ''} onChange={(event) => choose({ oauth_flows_json: event.target.value })} placeholder='{"clientCredentials":{"tokenUrl":"https://your-provider/token","scopes":{}}}' /><span className="hint">Supply your actual flow, URLs and available scopes. Leave empty to keep configuration pending.</span></label>}
        {choice.authentication === 'openid_connect' && <label>OpenID Connect discovery URL<input value={choice.openid_connect_url || ''} onChange={(event) => choose({ openid_connect_url: event.target.value })} placeholder="https://your-provider/.well-known/openid-configuration" /></label>}
        {choice.authentication === 'custom' && <label>Describe the custom authentication mechanism<textarea rows={3} value={choice.custom_description || ''} onChange={(event) => choose({ custom_description: event.target.value })} /><span className="hint">Saved as design metadata; a standard OpenAPI security scheme will not be inferred.</span></label>}
        {choice.authentication === 'unspecified' && <p>The choice will be saved, but authentication remains unresolved.</p>}
        <button type="button" className="primary" onClick={saveSecurity}>Save choice and regenerate</button>
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
