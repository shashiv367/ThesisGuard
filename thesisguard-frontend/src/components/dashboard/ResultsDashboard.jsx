import { KPIGrid } from './KPIGrid'
import { ReportTable } from './ReportTable'

export function ResultsDashboard({ report, metrics }) {
  if (!report) return null

  return (
    <section className="results-section">
      <div className="results-header">
        <div>
          <h2>Your results</h2>
          <div className="results-subtitle">
            {report.length} section{report.length !== 1 ? 's' : ''} analysed — review each row for details.
          </div>
        </div>
      </div>

      <KPIGrid metrics={metrics} reportLength={report.length} />
      <ReportTable report={report} />
    </section>
  )
}
