import { useState } from 'react'
import example from './example.json'

export default function useQualityEvaluation() {
  const [input, setInput] = useState('')
  const [result, setResult] = useState(null)
  const [history, setHistory] = useState([])
  const [busy, setBusy] = useState(false)
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
      payload = JSON.parse(input)
      if (!payload || Array.isArray(payload) || typeof payload.project_id !== 'string' || !payload.project_id.trim()) throw new Error('Include a non-empty project_id in the request object.')
      for (const key of ['architecture', 'database', 'api_component_design']) {
        if (!payload[key] || typeof payload[key] !== 'object' || Array.isArray(payload[key])) throw new Error(`Include a ${key} object.`)
      }
    } catch (err) { setError(`Check your JSON: ${err.message}`); return }
    setBusy(true)
    try {
      const response = await fetch('/quality-evaluation/evaluate', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload), signal: AbortSignal.timeout(180000),
      })
      const data = await response.json().catch(() => null)
      if (!response.ok) {
        const detail = Array.isArray(data?.detail) ? data.detail.map((item) => `${item.loc.join('.')}: ${item.msg}`).join('\n') : data?.detail
        throw new Error(typeof detail === 'string' ? detail : `Evaluation failed (${response.status}).`)
      }
      if (!data?.metrics || !Array.isArray(data.findings) || !Array.isArray(data.rule_results) || !Array.isArray(data.metrics.category_summaries)) throw new Error('Unexpected response from the backend.')
      setResult(data)
      setHistory((previous) => [data, ...previous].slice(0, 20))
      setEditor(false)
    } catch (err) {
      setError(err.name === 'TimeoutError' ? 'Evaluation timed out. Please try again.' : err instanceof TypeError ? 'Cannot reach the backend. Start it on port 8000 and try again.' : err.message)
    } finally { setBusy(false) }
  }
  function exportResult() {
    const url = URL.createObjectURL(new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' }))
    const link = document.createElement('a')
    link.href = url; link.download = `${result.evaluation_id}.json`; link.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  }
  return { input, setInput, result, setResult, history, busy, error, editor, setEditor, theme, toggleTheme, loadExample, evaluate, exportResult }
}
