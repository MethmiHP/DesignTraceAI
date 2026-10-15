import { useState } from 'react'
import example from './banking-example.json'
import { securityGaps, resolveSecurity } from './securityResolution'

const pretty = (value) => JSON.stringify(value, null, 2)
export default function useApiDesign() {
  const [inputJson, setInputJson] = useState('')
  let project = ''
  try {
    const value = JSON.parse(inputJson)?.project_id
    if (typeof value === 'string') project = value
  } catch { /* Keep incomplete JSON editable. */ }
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [view, setView] = useState('Context')
  const [submitted, setSubmitted] = useState(null)
  const [securityChoices, setSecurityChoices] = useState({})
  const gaps = securityGaps(result)

  function updateInput(value) {
    setInputJson(value)
    setSecurityChoices({})
    setResult(null)
    setSubmitted(null)
    setError('')
  }

  function loadExample() {
    updateInput(pretty(example))
    setView('Context')
  }

  function formatInput() {
    try {
      setInputJson(pretty(JSON.parse(inputJson)))
      setError('')
    } catch (err) {
      setError(`Invalid JSON: ${err.message}`)
    }
  }

  async function saveSecurity() {
    try {
      const payload = resolveSecurity(submitted, gaps, securityChoices)
      setInputJson(pretty(payload))
      await generate(null, payload)
    } catch (err) { setError(err.message) }
  }

  async function generate(event, resolvedPayload) {
    event?.preventDefault()
    if (busy) return
    setError('')
    setResult(null)
    let payload
    try {
      try { payload = resolvedPayload || JSON.parse(inputJson) } catch (err) { throw new Error(`Invalid JSON: ${err.message}`, { cause: err }) }
      if (!payload || typeof payload !== 'object' || Array.isArray(payload)) throw new Error('Paste one JSON object containing the complete design request.')
      if (typeof payload.project_id !== 'string' || !payload.project_id.trim()) throw new Error('project_id must be a non-empty string.')
      if (!Array.isArray(payload.functional_requirements) || !payload.functional_requirements.length) throw new Error('functional_requirements must contain at least one requirement.')
      if (payload.functional_requirements.some((item) => typeof item?.requirement_id !== 'string' || !item.requirement_id.trim() || typeof item?.statement !== 'string' || !item.statement.trim())) throw new Error('Every requirement must have a non-empty requirement_id and statement.')
      if (new Set(payload.functional_requirements.map((item) => item.requirement_id)).size !== payload.functional_requirements.length) throw new Error('Each requirement needs a unique ID.')
      if (!Array.isArray(payload.architecture?.elements) || !payload.architecture.elements.length) throw new Error('architecture.elements must contain at least one element.')
      if (!Array.isArray(payload.database?.entities) || !payload.database.entities.length) throw new Error('database.entities must contain at least one entity.')
    } catch (err) { setError(err.message); return }
    setBusy(true)
    try {
      const response = await fetch('/api-component/design', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload), signal: AbortSignal.timeout(180000),
      })
      const body = await response.json().catch(() => null)
      if (!response.ok) {
        const detail = Array.isArray(body?.detail) ? body.detail.map((item) => `${item.loc.join('.')}: ${item.msg}`).join('\n') : body?.detail
        throw new Error(detail || `Request failed (${response.status}). Check that the backend is running on port 8000.`)
      }
      const listFields = ['api_operations', 'responsibilities', 'semantic_extractions', 'requirement_to_api_mapping']
      if (!body || listFields.some((field) => !Array.isArray(body[field])) || !Array.isArray(body.validation?.issues)) {
        throw new Error('The backend returned an unexpected response.')
      }
      setResult(body)
      setSubmitted(payload)
      setSecurityChoices({})
      setView(securityGaps(body).length ? 'Context' : 'API Design')
    } catch (err) {
      setError(err.name === 'TimeoutError' ? 'The request timed out. Please try again.' : err instanceof TypeError ? 'Could not connect to the backend. Start the API on port 8000 and try again.' : err.message)
    } finally { setBusy(false) }
  }

  function download() {
    const url = URL.createObjectURL(new Blob([pretty(result.openapi_document)], { type: 'application/json' }))
    const link = document.createElement('a')
    link.href = url
    link.download = 'openapi.json'
    link.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  }

  return { gaps, securityChoices, setSecurityChoices, saveSecurity, inputJson, updateInput, formatInput, project, result, error, busy, view, setView, submitted, loadExample, generate, download }
}
