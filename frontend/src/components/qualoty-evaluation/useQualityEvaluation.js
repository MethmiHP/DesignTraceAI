import { useState } from 'react'
import example from './example.json'
import { requestJson, waitForEvaluation } from './evaluationClient'

export default function useQualityEvaluation() {
  const [input, setInput] = useState('')
  const [result, setResult] = useState(null)
  const [history, setHistory] = useState([])
  const [busy, setBusy] = useState(false)
  const [progress, setProgress] = useState(null)
  const [pendingJob, setPendingJob] = useState(() => {
    try { return sessionStorage.getItem('quality-pending-job') || '' } catch { return '' }
  })
  function rememberJob(id) {
    setPendingJob(id)
    try {
      if (id) sessionStorage.setItem('quality-pending-job', id)
      else sessionStorage.removeItem('quality-pending-job')
    } catch { /* Resuming still works in this page session. */ }
  }
  const [error, setError] = useState('')
  const [editor, setEditor] = useState(false)
  const [theme, setTheme] = useState(() => {
    try { return localStorage.getItem('quality-theme') === 'light' ? 'light' : 'dark' } catch { return 'dark' }
  })
  function toggleTheme() {
    const next = theme === 'dark' ? 'light' : 'dark'
    setTheme(next)
    try { localStorage.setItem('quality-theme', next) } catch { /* Theme still works without storage. */ }
  }
  function loadExample() { setInput(JSON.stringify(example, null, 2)); setError('') }
  async function evaluate(event) {
    event.preventDefault()
    if (busy) return
    setError('')
    let payload
    try {
      if (!pendingJob) {
      payload = JSON.parse(input)
      if (!payload || Array.isArray(payload) || typeof payload.project_id !== 'string' || !payload.project_id.trim()) throw new Error('Include a non-empty project_id in the request object.')
      for (const key of ['architecture', 'database', 'api_component_design']) {
        if (!payload[key] || typeof payload[key] !== 'object' || Array.isArray(payload[key])) throw new Error(`Include a ${key} object.`)
      }
      }
    } catch (err) { setError(`Check your JSON: ${err.message}`); return }
    setBusy(true)
    try {
      let jobId = pendingJob
      if (!jobId) {
        const job = await requestJson('/quality-evaluation/jobs', {
          method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
        })
        if (!job?.job_id) throw new Error('The backend did not return an evaluation job ID.')
        jobId = job.job_id
        rememberJob(jobId)
        setProgress(job)
      }
      const data = await waitForEvaluation(jobId, setProgress)
      if (!data?.metrics || !Array.isArray(data.findings) || !Array.isArray(data.rule_results) || !Array.isArray(data.metrics.category_summaries)) throw new Error('Unexpected response from the backend.')
      rememberJob('')
      setResult(data)
      setHistory((previous) => [data, ...previous].slice(0, 20))
      setEditor(false)
    } catch (err) {
      if (err.terminal) rememberJob('')
      setError(err.name === 'TimeoutError' ? 'Connection timed out. If a job was accepted, use Resume evaluation to check it without starting again.' : err instanceof TypeError ? 'Cannot reach the backend. Reconnect and resume the evaluation.' : err.message)
    } finally { setBusy(false) }
  }
  async function exportResult() {
    if (!result) return
    try {
      const { exportQualityPdf } = await import('./exportQualityPdf')
      exportQualityPdf(result)
    } catch {
      setError('Could not export the PDF. Please try again.')
      setEditor(true)
    }
  }
  return { pendingJob, progress, input, setInput, result, setResult, history, busy, error, editor, setEditor, theme, toggleTheme, loadExample, evaluate, exportResult }
}
