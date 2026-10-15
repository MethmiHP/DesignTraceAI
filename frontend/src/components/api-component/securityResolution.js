export function securityGaps(result) {
  return (result?.validation?.issues || []).filter((issue) => issue.code === 'SECURITY_CONFIGURATION_REQUIRED' && /^functional_requirements\.\d+\.security\.authentication$/.test(issue.field || ''))
}

export function resolveSecurity(payload, gaps, choices) {
  const updated = structuredClone(payload)
  for (const gap of gaps) {
    const index = Number(gap.field.split('.')[1])
    const requirement = updated.functional_requirements[index]
    const choice = choices[gap.field]
    if (!choice || !['bearer', 'basic', 'api_key'].includes(choice.authentication)) throw new Error(`Choose an authentication mechanism for ${requirement.requirement_id}.`)
    if (choice.authentication === 'api_key' && (!/^[A-Za-z0-9_-]+$/.test(choice.api_key_name || '') || !['header', 'query', 'cookie'].includes(choice.api_key_location))) throw new Error('Enter an API key parameter name and location.')
    requirement.security = { ...(requirement.security || updated.security || {}), ...choice }
  }
  return updated
}
