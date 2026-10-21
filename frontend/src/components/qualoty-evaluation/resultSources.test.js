import { test } from 'node:test'
import assert from 'node:assert/strict'
import { resultSource, sourceCounts } from './resultSources.js'

test('uses actual provider metadata and distinguishes skipped failures', () => {
  const results = [
    { check_type: 'deterministic', status: 'PASS' },
    { check_type: 'semantic', provider: 'gemini', status: 'PASS' },
    { check_type: 'semantic', provider: 'groq', status: 'FAIL' },
    { check_type: 'semantic', provider: null, status: 'SKIPPED' },
    { check_type: 'semantic', provider: 'groq', status: 'SKIPPED' },
  ]
  assert.deepEqual(sourceCounts(results), { Rules: 1, Gemini: 1, Groq: 2, 'No LLM result': 1 })
  assert.equal(resultSource({ check_type: 'semantic', status: 'PASS' }), 'Not recorded')
  assert.equal(resultSource(undefined), 'Not recorded')
})
