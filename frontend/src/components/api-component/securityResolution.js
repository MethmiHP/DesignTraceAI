export function securityGaps(result) {
  return (result?.validation?.issues || []).filter((issue) => issue.code === 'SECURITY_CONFIGURATION_REQUIRED' && /^functional_requirements\.\d+\.security\.authentication$/.test(issue.field || ''))
}

export function resolveSecurity(payload, gaps, choice) {
  const updated = structuredClone(payload)
  if (!['bearer', 'basic', 'api_key', 'oauth2', 'openid_connect', 'mutual_tls', 'custom', 'unspecified'].includes(choice.authentication)) throw new Error('Choose an authentication mechanism.')
  const policy = { authentication: choice.authentication }
  if (choice.authentication === 'api_key') {
    if (!/^[A-Za-z0-9_-]+$/.test(choice.api_key_name || '') || !['header', 'query', 'cookie'].includes(choice.api_key_location)) throw new Error('Enter an API key parameter name and location.')
    Object.assign(policy, { api_key_name: choice.api_key_name, api_key_location: choice.api_key_location })
  }
  if (choice.authentication === 'oauth2' && choice.oauth_flows_json?.trim()) {
    try { policy.oauth_flows = JSON.parse(choice.oauth_flows_json) } catch { throw new Error('OAuth flows must be valid JSON.') }
  }
  if (choice.authentication === 'openid_connect') policy.openid_connect_url = choice.openid_connect_url || null
  if (choice.authentication === 'custom') policy.custom_description = choice.custom_description || null
  // Store the shared choice once. Explicit per-requirement overrides remain authoritative.
  updated.security = { ...updated.security, ...policy }
  for (const gap of gaps) {
    const index = Number(gap.field.split('.')[1])
    const requirement = updated.functional_requirements[index]
    if (requirement.security) requirement.security = { ...requirement.security, ...policy }
  }
  return updated
}
