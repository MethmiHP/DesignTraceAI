export async function requestJson(url, options = {}) {
  const response = await fetch(url, { ...options, signal: AbortSignal.timeout(30000) })
  const body = await response.json()
  if (!response.ok) {
    const detail = Array.isArray(body?.detail) ? body.detail.map((item) => `${item.loc.join('.')}: ${item.msg}`).join('\n') : body?.detail
    const error = new Error(detail || `Request failed (${response.status}).`)
    error.status = response.status
    throw error
  }
  return body
}

export async function waitForDesign(jobId, { request = requestJson, sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms)) } = {}) {
  let failures = 0
  for (;;) {
    let job
    try {
      job = await request(`/api-component/jobs/${jobId}`)
      failures = 0
    } catch (error) {
      if ((error.status && error.status < 500) || ++failures >= 3) throw error
      await sleep(2000)
      continue
    }
    if (job.status === 'completed') return job.result
    if (job.status === 'failed') {
      const error = new Error(job.error || 'Generation failed.')
      error.jobFailed = true
      throw error
    }
    if (!['queued', 'running'].includes(job.status)) throw new Error('Unexpected job status.')
    await sleep(1500)
  }
}
