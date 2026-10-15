import { test } from 'node:test'
import assert from 'node:assert/strict'
import { securityGaps, resolveSecurity } from './securityResolution.js'

test('resolution requires a choice and preserves explicit policies and access rules', () => {
  const payload = {
    security: { authentication: 'unspecified', roles: ['customer'], access_rules: ['Own accounts only'] },
    non_functional_requirements: [{ statement: 'Authentication required' }],
    functional_requirements: [{ requirement_id: 'FR-1' }, { requirement_id: 'FR-2', security: { authentication: 'basic' } }],
  }
  const field = 'functional_requirements.0.security.authentication'
  const gaps = securityGaps({ validation: { issues: [{ code: 'SECURITY_CONFIGURATION_REQUIRED', field }] } })
  assert.throws(() => resolveSecurity(payload, gaps, {}), /Choose an authentication/)
  const resolved = resolveSecurity(payload, gaps, { [field]: { authentication: 'bearer' } })
  assert.deepEqual(resolved.functional_requirements[0].security, { ...payload.security, authentication: 'bearer' })
  assert.deepEqual(resolved.functional_requirements[1], payload.functional_requirements[1])
  assert.deepEqual(resolved.non_functional_requirements, payload.non_functional_requirements)
  assert.equal(payload.functional_requirements[0].security, undefined)
  assert.throws(() => resolveSecurity(payload, gaps, { [field]: { authentication: 'api_key' } }), /parameter name and location/)
  const apiKey = resolveSecurity(payload, gaps, { [field]: { authentication: 'api_key', api_key_name: 'X-Customer-Key', api_key_location: 'header' } })
  assert.equal(apiKey.functional_requirements[0].security.api_key_name, 'X-Customer-Key')
})
