import { test } from 'node:test'
import assert from 'node:assert/strict'
import { waitForDesign } from './designClient.js'

test('waits beyond three minutes without submitting another job', async () => {
  let polls = 0
  let elapsed = 0
  const result = await waitForDesign('job-1', {
    request: async (url) => {
      assert.equal(url, '/api-component/jobs/job-1')
      return ++polls <= 130 ? { status: 'running' } : { status: 'completed', result: { api_operations: [] } }
    },
    sleep: async (ms) => { elapsed += ms },
  })
  assert.ok(elapsed > 180000)
  assert.deepEqual(result, { api_operations: [] })
})

test('reports failed jobs and retries transient polling errors', async () => {
  let calls = 0
  await assert.rejects(waitForDesign('job', {
    request: async () => {
      if (++calls === 1) throw new TypeError('connection interrupted')
      return { status: 'failed', error: 'Generation failed' }
    }, sleep: async () => {},
  }), /Generation failed/)
  assert.equal(calls, 2)
})
