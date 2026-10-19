import { jsPDF } from 'jspdf'

export function buildQualityPdf(report) {
  const doc = new jsPDF({ unit: 'mm', format: 'a4' })
  const margin = 18
  const width = 174
  let y = 34
  const percent = (value) => value == null ? 'Not applicable' : `${value}%`
  const clean = (value) => String(value ?? '').replace(/[\u2010-\u2015]/g, '-').replace(/[\u2018\u2019]/g, "'").replace(/[\u201c\u201d]/g, '"')
  function header() {
    doc.setFillColor(52, 120, 246)
    doc.roundedRect(margin, 12, 7, 7, 2, 2, 'F')
    doc.setFont('helvetica', 'bold'); doc.setFontSize(10); doc.setTextColor(40, 35, 65)
    doc.text('DesignTrace AI', margin + 10, 17)
    doc.setDrawColor(222, 220, 235); doc.line(margin, 23, 192, 23)
  }
  function room(height) {
    if (y + height > 277) { doc.addPage(); header(); y = 34 }
  }
  function text(value, { size = 10, bold = false, color = [65, 61, 80], gap = 3 } = {}) {
    doc.setFont('helvetica', bold ? 'bold' : 'normal'); doc.setFontSize(size)
    const lines = doc.splitTextToSize(clean(value), width)
    const step = size * 0.48
    for (const line of lines) {
      room(step)
      doc.setFont('helvetica', bold ? 'bold' : 'normal'); doc.setFontSize(size); doc.setTextColor(...color)
      doc.text(line, margin, y); y += step
    }
    y += gap
  }
  function section(title) {
    room(22); y += 3
    text(title, { size: 13, bold: true, color: [88, 70, 175], gap: 5 })
  }
  header()
  doc.setProperties({ title: `Quality Evaluation - ${report.project_id}`, author: 'DesignTrace AI', subject: report.evaluation_id })
  text('Quality Evaluation Report', { size: 22, bold: true, color: [32, 28, 50], gap: 6 })
  text(`Project: ${report.project_id}`)
  text(`Evaluation: ${report.evaluation_id}`)
  text(`Generated: ${report.generated_at}`)
  section('Evaluation overview')
  const m = report.metrics
  text(`Quality pass rate: ${percent(m.quality_pass_percentage)}   |   NFR coverage: ${percent(m.nfr_coverage_percentage)}`, { bold: true })
  text(`Rules: ${m.total_applicable_rules} applicable / ${m.passed_rules} passed / ${m.failed_rules} failed / ${m.skipped_rules} skipped`)
  text(`NFRs: ${m.evaluated_nfrs} evaluated / ${m.applicable_nfrs} applicable`)
  text(`Findings: ${report.findings.length} total / ${report.findings.filter((f) => ['CRITICAL', 'HIGH'].includes(f.severity)).length} high or critical`)
  text(report.summary)
  section('NFR category results')
  for (const c of m.category_summaries) {
    room(20)
    text(`${c.category} - ${percent(c.pass_percentage)} pass rate`, { bold: true, gap: 1 })
    text(`${c.passed_rules}/${c.applicable_rules} rules passed; ${c.failed_rules} failed; ${c.skipped_rules} skipped. NFR coverage: ${percent(c.nfr_coverage_percentage)}.`, { size: 9, gap: 5 })
  }
  section('Findings and recommendations')
  if (!report.findings.length) text('No findings were returned by this evaluation.')
  for (const [index, f] of report.findings.entries()) {
    room(25)
    text(`${index + 1}. ${f.rule_id} | ${f.severity} | ${f.quality_attribute}`, { bold: true })
    text(f.rationale)
    text(`Artifact: ${f.artifact_type}. Check: ${f.check_type}. NFRs: ${f.affected_nfr_ids.join(', ') || 'None linked'}.`, { size: 9 })
    text('Evidence', { bold: true })
    for (const evidence of f.evidence) text(`- ${evidence}`, { size: 9 })
    if (!f.evidence.length) text('No evidence supplied.', { size: 9 })
    text(`Recommendation: ${f.recommendation}`)
  }
  if (report.finding_groups?.length) {
    section('Related findings')
    for (const g of report.finding_groups) {
      room(20); text(`${g.title} | ${g.severity}`, { bold: true }); text(g.summary)
      text(`Rules: ${g.rule_ids.join(', ')}`, { size: 9 })
      for (const recommendation of g.recommendations) text(`- ${recommendation}`)
    }
  }
  section('Rule evaluation details')
  if (!report.rule_results.length) text('No rules were applicable.')
  for (const r of report.rule_results) {
    room(20); text(`${r.rule_id} | ${r.status} | ${r.check_type}`, { bold: true })
    text(r.rationale)
    if (r.provider) text(`Provider: ${r.provider}`, { size: 9 })
  }
  const pages = doc.getNumberOfPages()
  for (let page = 1; page <= pages; page++) {
    doc.setPage(page); doc.setDrawColor(222, 220, 235); doc.line(margin, 283, 192, 283)
    doc.setFont('helvetica', 'normal'); doc.setFontSize(8); doc.setTextColor(110, 105, 125)
    doc.text('DesignTrace AI | Quality Evaluation', margin, 289)
    doc.text(`${page} / ${pages}`, 192, 289, { align: 'right' })
  }
  return doc
}

export function exportQualityPdf(report) {
  buildQualityPdf(report).save(`${report.evaluation_id.replace(/[^a-zA-Z0-9_-]/g, '_')}.pdf`)
}
