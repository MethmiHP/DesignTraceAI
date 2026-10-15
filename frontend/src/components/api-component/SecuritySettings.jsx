export default function SecuritySettings({ policy, onChange }) {
  const update = (field, value) => onChange({ ...policy, [field]: value })
  return <details><summary>Security requirements <span>ACCESS</span></summary>
    <p className="hint">Applies to all requirements in this form. Describe the generated API’s security here; do not enter real tokens or API keys.</p>
    <label>Authentication<select value={policy.authentication} onChange={(event) => update('authentication', event.target.value)}>
      <option value="unspecified">Not specified — needs review</option><option value="none">Public — no authentication</option><option value="bearer">Bearer token</option><option value="basic">HTTP Basic</option><option value="api_key">API key</option>
    </select></label>
    {policy.authentication === 'api_key' && <><label>API key parameter name<input required pattern="[A-Za-z0-9_-]+" value={policy.api_key_name} onChange={(event) => update('api_key_name', event.target.value)} /></label><label>API key location<select value={policy.api_key_location} onChange={(event) => update('api_key_location', event.target.value)}><option value="header">Header</option><option value="query">Query</option><option value="cookie">Cookie</option></select></label></>}
    <label>Allowed roles (comma-separated)<input placeholder="customer, administrator" value={policy.roles.join(',')} onChange={(event) => update('roles', event.target.value.split(','))} /></label>
    <label>Access rules (one per line)<textarea rows={3} placeholder="Customers may access only their own bank accounts." value={policy.access_rules.join('\n')} onChange={(event) => update('access_rules', event.target.value.split('\n'))} /></label>
    <p className="hint">These rules document required authorization. They must be enforced when the generated API is implemented.</p>
  </details>
}
