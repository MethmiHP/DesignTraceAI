export default function SecurityDetails({ operation, spec, document }) {
  const policy = operation.security
  const requirements = spec.security ?? document?.security
  const schemes = document?.components?.securitySchemes || {}
  const names = [...new Set((requirements || []).flatMap((item) => Object.keys(item)))]
  const publicAccess = Array.isArray(requirements) && (requirements.length === 0 || requirements.some((item) => Object.keys(item).length === 0))
  const roles = policy?.roles || spec['x-required-roles'] || []
  const rules = policy?.access_rules || spec['x-access-rules'] || []
  return <section className="data-section"><h3>Security configuration</h3>
    {publicAccess ? <p className="notice">This endpoint is explicitly configured for public access. Authentication is not required.</p> : !names.length ? <p className="notice warning">Authentication has not been specified. Select a scheme or explicitly mark the API public in Design context → Security requirements, then regenerate.</p> : names.map((name) => {
      const scheme = schemes[name]
      if (!scheme) return <p className="error" key={name}>Missing security scheme definition: {name}</p>
      return <article className="inspector-card" key={name}><h3>Authentication required</h3><p>{scheme.type === 'http' ? scheme.scheme === 'bearer' ? 'Bearer token' : 'HTTP Basic' : scheme.type === 'apiKey' ? 'API key' : scheme.type}</p><p>{scheme.type === 'http' ? `Header: Authorization — ${scheme.scheme === 'bearer' ? 'Bearer <token>' : 'Basic <encoded credentials>'}` : scheme.type === 'apiKey' ? `${scheme.in}: ${scheme.name}` : scheme.description}</p></article>
    })}
    <div className="data-section"><h3>Allowed roles</h3>{roles.length ? <div className="mapping-list">{roles.map((role, i) => <code key={i}>{role}</code>)}</div> : <p className="muted">No role restrictions specified.</p>}</div>
    <div className="data-section"><h3>Authorization rules</h3>{rules.length ? <ul>{rules.map((rule, i) => <li key={i}>{rule}</li>)}</ul> : <p className="muted">No additional access rules specified.</p>}</div>
    <div className="data-section"><h3>Authentication and authorization errors</h3>{['401', '403'].filter((code) => operation.error_responses?.[code]).map((code) => <p key={code}><code>{code}</code> — {operation.error_responses[code]}</p>)}</div>
    <p className="hint">This is an API design specification. Token verification, role checks, and ownership checks still need runtime implementation.</p>
  </section>
}
