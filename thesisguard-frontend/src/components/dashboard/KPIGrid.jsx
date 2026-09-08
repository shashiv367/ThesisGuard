export function KPIGrid({ metrics, reportLength }) {
  const {
    maxSimilarityScore,
    exactMatchCount,
    semanticMatchCount,
    aiFlaggedCount
  } = metrics

  return (
    <div className="kpi-grid">
      <div className="kpi-card">
        <span className="kpi-title">Highest match</span>
        <span
          className="kpi-value"
          style={{
            color: maxSimilarityScore > 70
              ? '#962d22'
              : maxSimilarityScore > 40
              ? '#b45309'
              : '#16a34a'
          }}
        >
          {maxSimilarityScore.toFixed(1)}%
        </span>
        <span className="kpi-desc">Closest section to existing sources</span>
      </div>

      <div className="kpi-card">
        <span className="kpi-title">Overall result</span>
        <span className="kpi-value">
          {exactMatchCount > 0 ? (
            <span className="status-badge badge-exact">Copied text found</span>
          ) : semanticMatchCount > 0 ? (
            <span className="status-badge badge-semantic">Similar phrasing found</span>
          ) : (
            <span className="status-badge badge-none">Looks original</span>
          )}
        </span>
        <span className="kpi-desc">
          {exactMatchCount} exact · {semanticMatchCount} paraphrase
        </span>
      </div>

      <div className="kpi-card">
        <span className="kpi-title">Writing style</span>
        <span className="kpi-value">
          {aiFlaggedCount > 0 ? (
            <span className="status-badge badge-ai">{aiFlaggedCount} flagged</span>
          ) : (
            <span className="status-badge badge-none">Reads as human</span>
          )}
        </span>
        <span className="kpi-desc">AI-assisted writing signal (not definitive)</span>
      </div>

      <div className="kpi-card">
        <span className="kpi-title">Sections checked</span>
        <span className="kpi-value">{reportLength}</span>
        <span className="kpi-desc">Paragraphs analysed in this scan</span>
      </div>
    </div>
  )
}
