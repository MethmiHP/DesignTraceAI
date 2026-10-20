import { test } from 'node:test'
import assert from 'node:assert/strict'
import { waitForEvaluation } from './evaluationClient.js'

test('keeps polling beyond the old three-minute deadline without resubmitting', async () => {
  let calls = 0
  let simulatedElapsed = 0
  const result = { evaluation_id: 'QE-TEST' }
  const received = await waitForEvaluation('existing-job', () => {}, async (url) => {
    assert.equal(url, '/quality-evaluation/jobs/existing-job')
    return ++calls > 150 ? { status: 'completed', result } : { status: 'running' }
  }, async (ms) => { simulatedElapsed += ms })
  assert.equal(received, result)
  assert.ok(simulatedElapsed > 180000)
})

test('retries temporary poll failures and returns the original job result', async () => {
  let calls = 0
  const result = await waitForEvaluation('job', () => {}, async () => {
    if (++calls < 3) throw new TypeError('offline')
    return { status: 'completed', result: { ok: true } }
  }, async () => {})
  assert.deepEqual(result, { ok: true })
})

test('failed jobs are terminal and do not poll indefinitely', async () => {
  await assert.rejects(waitForEvaluation('job', () => {}, async () => ({ status: 'failed', error: 'Could not save report' }), async () => {}), { message: 'Could not save report', terminal: true })
})
