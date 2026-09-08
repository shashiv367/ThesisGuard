export function ReportTable({ report }) {
  return (
    <div className="table-wrapper">
      <table className="report-table">
        <thead>
          <tr>
            <th className="col-idx">#</th>
            <th className="col-text">Text excerpt</th>
            <th className="col-type">Match type</th>
            <th className="col-score">Similarity</th>
            <th className="col-ai">AI writing signal</th>
            <th className="col-tags">Topics</th>
            <th className="col-summary">Source summary</th>
          </tr>
        </thead>
        <tbody>
          {report.map((chunk, index) => {
            const matchType = chunk.match_type || 'none'

            // Determine best similarity score
            let scoreText = '—'
            let scoreClass = 'score-low'
            if (chunk.semantic_matches && chunk.semantic_matches.length > 0) {
              const sim = chunk.semantic_matches[0].similarity * 100
              scoreText = sim.toFixed(1) + '%'
              scoreClass = sim >= 70 ? 'score-high' : sim >= 50 ? 'score-medium' : 'score-low'
            } else if (matchType === 'exact') {
              scoreText = '100%'
              scoreClass = 'score-high'
            }

            const aiDetection = chunk.ai_detection

            // Human-readable match type labels
            const matchLabel = matchType === 'exact'
              ? 'Copied'
              : matchType === 'semantic'
              ? 'Paraphrase'
              : 'None'

            return (
              <tr key={index}>
                <td className="col-idx">{index + 1}</td>

                <td className="col-text">
                  <div className="text-snippet-box" title={chunk.text}>
                    {chunk.text.length > 90
                      ? chunk.text.substring(0, 90) + '…'
                      : chunk.text}
                  </div>
                </td>

                <td className="col-type">
                  <span className={`status-badge badge-${matchType}`}>
                    {matchLabel}
                  </span>
                </td>

                <td className="col-score">
                  <span className={`score-pill ${scoreClass}`}>
                    {scoreText}
                  </span>
                </td>

                <td className="col-ai">
                  {aiDetection ? (
                    <span
                      className={`status-badge ${aiDetection.label === 'AI-generated' ? 'badge-ai' : 'badge-human'}`}
                      title="AI writing detection is a probabilistic signal and can produce false positives. Use as a guide, not a verdict."
                    >
                      {aiDetection.formatted}
                    </span>
                  ) : (
                    <span style={{ color: '#b0bdcc' }}>—</span>
                  )}
                </td>

                <td className="col-tags">
                  {chunk.keyword_tags && chunk.keyword_tags.length > 0 ? (
                    <div className="tags-flex-wrap">
                      {chunk.keyword_tags.map((tag, i) => (
                        <span key={i} className="keyword-chip">{tag.keyword}</span>
                      ))}
                    </div>
                  ) : (
                    <span style={{ color: '#b0bdcc' }}>—</span>
                  )}
                </td>

                <td className="col-summary">
                  <div className="summary-text-block">
                    {chunk.source_summary || (
                      <span style={{ color: '#b0bdcc' }}>No matching source</span>
                    )}
                  </div>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
