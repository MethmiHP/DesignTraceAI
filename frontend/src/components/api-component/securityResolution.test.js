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
  const resolved = resolveSecurity(payload, gaps, { authentication: 'bearer' })
  assert.deepEqual(resolved.security, { ...payload.security, authentication: 'bearer' })
  assert.deepEqual(resolved.functional_requirements[1], payload.functional_requirements[1])
  assert.deepEqual(resolved.non_functional_requirements, payload.non_functional_requirements)
  assert.equal(payload.functional_requirements[0].security, undefined)
  assert.throws(() => resolveSecurity(payload, gaps, { authentication: 'api_key' }), /parameter name and location/)
  const apiKey = resolveSecurity(payload, gaps, { authentication: 'api_key', api_key_name: 'X-Customer-Key', api_key_location: 'header' })
  assert.equal(apiKey.security.api_key_name, 'X-Customer-Key')
})

for (const authentication of ['oauth2', 'openid_connect', 'mutual_tls', 'custom', 'unspecified']) {
  test(`shared ${authentication} choice is saved without guessing details`, () => {
    const payload = { functional_requirements: [{ requirement_id: 'FR-1' }, { requirement_id: 'FR-2' }] }
    const result = resolveSecurity(payload, [], { authentication })
    assert.equal(result.security.authentication, authentication)
    assert.deepEqual(result.functional_requirements, payload.functional_requirements)
  })
}
