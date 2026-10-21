export function resultSource(result) {
  if (!result) return 'Not recorded'
  if (result.check_type === 'deterministic') return 'Rules'
  const provider = result.provider?.toLowerCase()
  if (provider === 'gemini') return 'Gemini'
  if (provider === 'groq') return 'Groq'
  if (provider) return result.provider
  return result.status === 'SKIPPED' ? 'No LLM result' : 'Not recorded'
}

export function sourceCounts(results) {
  return results.reduce((counts, result) => {
    const source = resultSource(result)
    counts[source] = (counts[source] || 0) + 1
    return counts
  }, {})
}
