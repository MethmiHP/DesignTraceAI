const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

export async function requestJson(url, options = {}) {
  const response = await fetch(url, { ...options, signal: AbortSignal.timeout(30000) })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const detail = Array.isArray(data?.detail) ? data.detail.map((item) => `${item.loc.join('.')}: ${item.msg}`).join('\n') : data?.detail
    const error = new Error(typeof detail === 'string' ? detail : `Request failed (${response.status}).`)
    error.terminal = response.status === 404
    throw error
  }
  return data
}

export async function waitForEvaluation(jobId, onProgress, request = requestJson, delay = sleep) {
  let failures = 0
  // Each poll is short. There is no three-minute deadline for the whole job.
  for (;;) {
    let job
    try {
      job = await request(`/quality-evaluation/jobs/${encodeURIComponent(jobId)}`)
      failures = 0
    } catch (error) {
      if (error.terminal || ++failures >= 3) throw error
      await delay(2000)
      continue
    }
    onProgress(job)
    if (job.status === 'completed') return job.result
    if (job.status === 'failed') {
      const error = new Error(job.error || 'Evaluation failed.')
      error.terminal = true
      throw error
    }
    if (!['queued', 'running'].includes(job.status)) throw new Error('Unexpected evaluation status.')
    await delay(1500)
  }
}
