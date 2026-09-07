import { useState, useEffect } from 'react'
import './App.css'

// ============================================================================
// NOTE ON JWT STORAGE TRADEOFF FOR PROJECT REPORT:
// In this implementation, the JWT access token is stored in React memory state and
// persisted in localStorage. This allows user sessions to persist across page
// reloads and browser tabs without requiring re-authentication.
//
// Security Tradeoff: Storing tokens in localStorage leaves them accessible to
// any script running in the application origin, creating an exposure risk in the
// event of a Cross-Site Scripting (XSS) vulnerability.
//
// Recommended Production Alternative: Use secure, httpOnly, SameSite=Strict cookies
// issued directly by the backend server. httpOnly cookies are inaccessible to
// client-side JavaScript, effectively eliminating XSS-based token theft, though
// requiring CSRF defenses (e.g. SameSite cookie policy or anti-CSRF tokens).
// ============================================================================

function App() {
  // Auth state
  const [token, setToken] = useState(() => localStorage.getItem('thesisguard_token'))
  const [currentUser, setCurrentUser] = useState(() => {
    const saved = localStorage.getItem('thesisguard_user')
    return saved ? JSON.parse(saved) : null
  })
  const [authMode, setAuthMode] = useState('login') // 'login' | 'signup'
  const [authEmail, setAuthEmail] = useState('')
  const [authPassword, setAuthPassword] = useState('')
  const [authError, setAuthError] = useState(null)
  const [authLoading, setAuthLoading] = useState(false)

  // Scanner state
  const [mode, setMode] = useState('upload') // 'upload' | 'text'
  const [file, setFile] = useState(null)
  const [pastedText, setPastedText] = useState('')
  const [title, setTitle] = useState('')
  const [loading, setLoading] = useState(false)
  const [report, setReport] = useState(null)
  const [error, setError] = useState(null)

  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'

  const handleLogout = () => {
    setToken(null)
    setCurrentUser(null)
    localStorage.removeItem('thesisguard_token')
    localStorage.removeItem('thesisguard_user')
    setReport(null)
    setError(null)
  }

  const handleAuthSubmit = async (e) => {
    e.preventDefault()
    setAuthError(null)
    setAuthLoading(true)

    try {
      const endpoint = authMode === 'signup' ? `${baseUrl}/auth/signup` : `${baseUrl}/auth/login`
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: authEmail, password: authPassword }),
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Authentication failed')
      }

      setToken(data.access_token)
      setCurrentUser(data.user)
      localStorage.setItem('thesisguard_token', data.access_token)
      localStorage.setItem('thesisguard_user', JSON.stringify(data.user))
      setAuthPassword('')
    } catch (err) {
      setAuthError(err.message)
    } finally {
      setAuthLoading(false)
    }
  }

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setError(null)
    }
  }

  const handleRemoveFile = (e) => {
    e.stopPropagation()
    setFile(null)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (mode === 'upload' && !file) return
    if (mode === 'text' && !pastedText.trim()) return

    setLoading(true)
    setError(null)
    setReport(null)

    try {
      let response
      const authHeaders = {
        'Authorization': `Bearer ${token}`
      }

      if (mode === 'upload') {
        const formData = new FormData()
        formData.append('file', file)
        response = await fetch(`${baseUrl}/upload`, {
          method: 'POST',
          headers: authHeaders,
          body: formData,
        })
      } else {
        response = await fetch(`${baseUrl}/check-text`, {
          method: 'POST',
          headers: {
            ...authHeaders,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            text: pastedText,
            title: title.trim() || undefined,
          }),
        })
      }
      
      if (!response.ok) {
        if (response.status === 401) {
          handleLogout()
          throw new Error('Your session has expired. Please sign in again.')
        }
        let errMessage = `API error: ${response.statusText}`
        try {
          const errData = await response.json()
          if (errData && errData.detail) {
            errMessage = errData.detail
          }
        } catch {
          // fallback to statusText
        }
        throw new Error(errMessage)
      }
      
      const data = await response.json()
      setReport(data.report)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const isSubmitDisabled = loading || (mode === 'upload' ? !file : !pastedText.trim())

  // Compute summary KPI metrics from report chunks
  let maxSimilarityScore = 0
  let exactMatchCount = 0
  let semanticMatchCount = 0
  let aiFlaggedCount = 0

  if (report && report.length > 0) {
    report.forEach(chunk => {
      if (chunk.match_type === 'exact') exactMatchCount++
      if (chunk.match_type === 'semantic') semanticMatchCount++
      if (chunk.ai_detection && chunk.ai_detection.label === 'AI-generated') aiFlaggedCount++
      
      if (chunk.semantic_matches && chunk.semantic_matches.length > 0) {
        const topScore = chunk.semantic_matches[0].similarity * 100
        if (topScore > maxSimilarityScore) maxSimilarityScore = topScore
      } else if (chunk.match_type === 'exact') {
        maxSimilarityScore = 100
      }
    })
  }

  return (
    <div className="app-wrapper">
      {/* 1. TOP NAVIGATION BAR */}
      <nav className="app-navbar">
        <div className="navbar-inner">
          <div className="brand-group">
            <div className="brand-icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                <path d="m9 12 2 2 4-4"/>
              </svg>
            </div>
            <div className="brand-name">
              Thesis<span>Guard</span>
            </div>
            <span className="brand-badge">Engine v2.0</span>
          </div>

          {token && currentUser ? (
            <div className="user-profile-bar">
              <div className="user-avatar-chip">
                <div className="avatar-circle">
                  {currentUser.email ? currentUser.email.charAt(0).toUpperCase() : 'U'}
                </div>
                <span className="user-email-text" title={currentUser.email}>
                  {currentUser.email}
                </span>
              </div>
              <button type="button" className="nav-signout-btn" onClick={handleLogout}>
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                  <polyline points="16 17 21 12 16 7"/>
                  <line x1="21" y1="12" x2="9" y2="12"/>
                </svg>
                Sign Out
              </button>
            </div>
          ) : (
            <div className="user-profile-bar">
              <span className="brand-badge" style={{ background: '#f1f5f9', color: '#475569', borderColor: '#cbd5e1' }}>
                Guest Access
              </span>
            </div>
          )}
        </div>
      </nav>

      {/* 2. MAIN APPLICATION WORKSPACE */}
      <main className="app-main">
        {/* HERO SECTION */}
        <section className="hero-section">
          <div className="hero-tag">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
            </svg>
            Exact LSH &bull; pgvector Embeddings &bull; AI Classifier
          </div>
          <h1 className="hero-title">
            Academic Integrity & <span>Plagiarism Engine</span>
          </h1>
          <p className="hero-subtitle">
            Verify academic manuscripts, dissertations, and research drafts using multi-layer detection: 
            verbatim minhash indexing, semantic vector similarity, and synthetic AI text classification.
          </p>
        </section>

        {/* 3. AUTHENTICATION (Login / Signup) */}
        {!token ? (
          <section className="auth-card">
            <div className="auth-header">
              <h3>{authMode === 'login' ? 'Sign In to Your Workspace' : 'Create ThesisGuard Account'}</h3>
              <p>Sign in to access document scanning and generate persistent audit reports.</p>
            </div>

            <div className="segmented-control" role="tablist">
              <button
                type="button"
                role="tab"
                aria-selected={authMode === 'login'}
                className={`segmented-btn ${authMode === 'login' ? 'segmented-btn-active' : ''}`}
                onClick={() => { setAuthMode('login'); setAuthError(null); }}
              >
                Sign In
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={authMode === 'signup'}
                className={`segmented-btn ${authMode === 'signup' ? 'segmented-btn-active' : ''}`}
                onClick={() => { setAuthMode('signup'); setAuthError(null); }}
              >
                Create Account
              </button>
            </div>

            <form onSubmit={handleAuthSubmit} className="auth-form-body">
              <div className="form-field">
                <label className="form-label" htmlFor="auth-email">Institutional or Academic Email</label>
                <input
                  id="auth-email"
                  type="email"
                  required
                  className="form-input"
                  placeholder="scholar@university.edu"
                  value={authEmail}
                  onChange={(e) => setAuthEmail(e.target.value)}
                  disabled={authLoading}
                />
              </div>

              <div className="form-field">
                <label className="form-label" htmlFor="auth-password">Account Password</label>
                <input
                  id="auth-password"
                  type="password"
                  required
                  minLength={6}
                  className="form-input"
                  placeholder="Minimum 6 characters"
                  value={authPassword}
                  onChange={(e) => setAuthPassword(e.target.value)}
                  disabled={authLoading}
                />
              </div>

              <button type="submit" className="btn-primary-gradient" disabled={authLoading}>
                {authLoading && <span className="spinner"></span>}
                {authLoading ? 'Authenticating...' : (authMode === 'login' ? 'Sign In' : 'Create Account')}
              </button>
            </form>

            {authError && (
              <div className="error-banner">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="12" y1="8" x2="12" y2="12"/>
                  <line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                {authError}
              </div>
            )}
          </section>
        ) : (
          /* 4. SCANNER CARD (Upload File vs Paste Text) */
          <section className="scanner-card">
            <div className="scanner-nav-container">
              <div className="scanner-nav" role="tablist">
                <button
                  type="button"
                  role="tab"
                  aria-selected={mode === 'upload'}
                  className={`scanner-tab ${mode === 'upload' ? 'scanner-tab-active' : ''}`}
                  onClick={() => { setMode('upload'); setError(null); }}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="17 8 12 3 7 8"/>
                    <line x1="12" y1="3" x2="12" y2="15"/>
                  </svg>
                  Upload Document
                </button>
                <button
                  type="button"
                  role="tab"
                  aria-selected={mode === 'text'}
                  className={`scanner-tab ${mode === 'text' ? 'scanner-tab-active' : ''}`}
                  onClick={() => { setMode('text'); setError(null); }}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                    <line x1="16" y1="13" x2="8" y2="13"/>
                    <line x1="16" y1="17" x2="8" y2="17"/>
                    <polyline points="10 9 9 9 8 9"/>
                  </svg>
                  Paste Text
                </button>
              </div>
            </div>

            <form onSubmit={handleSubmit}>
              {mode === 'upload' ? (
                <div>
                  {!file ? (
                    <div className="dropzone-container">
                      <input 
                        type="file" 
                        accept=".pdf,.docx" 
                        onChange={handleFileChange}
                        disabled={loading}
                        className="file-hidden-input"
                      />
                      <div className="dropzone-icon">
                        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/>
                          <path d="M12 12v9"/>
                          <path d="m16 16-4-4-4 4"/>
                        </svg>
                      </div>
                      <p className="dropzone-title">Click or Drag Manuscript to Upload</p>
                      <p className="dropzone-hint">Supported document formats: PDF (.pdf) and Microsoft Word (.docx)</p>
                    </div>
                  ) : (
                    <div style={{ textAlign: 'center' }}>
                      <div className="selected-file-chip">
                        <span className="file-info-icon">
                          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                            <polyline points="14 2 14 8 20 8"/>
                          </svg>
                        </span>
                        <span className="file-info-name">{file.name}</span>
                        <button 
                          type="button" 
                          className="file-remove-btn" 
                          onClick={handleRemoveFile} 
                          title="Remove file"
                        >
                          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <line x1="18" y1="6" x2="6" y2="18"/>
                            <line x1="6" y1="6" x2="18" y2="18"/>
                          </svg>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-mode-box">
                  <div className="form-field">
                    <label className="form-label" htmlFor="doc-title">Document Title (Optional)</label>
                    <input
                      id="doc-title"
                      type="text"
                      className="form-input"
                      placeholder="e.g. Chapter 3: Methodology and Statistical Framework"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      disabled={loading}
                    />
                  </div>

                  <div className="form-field">
                    <label className="form-label">Manuscript Text to Check</label>
                    <div className="textarea-wrapper">
                      <textarea
                        className="modern-textarea"
                        placeholder="Paste research text, abstract, or literature review to inspect for plagiarism and AI-generated signals..."
                        value={pastedText}
                        onChange={(e) => setPastedText(e.target.value)}
                        disabled={loading}
                        rows={8}
                      />
                      <span className="textarea-stats">
                        {pastedText.trim() ? `${pastedText.trim().split(/\s+/).length} words &bull; ` : ''}{pastedText.length} chars
                      </span>
                    </div>
                  </div>
                </div>
              )}

              <div className="scanner-actions">
                <button type="submit" className="btn-primary-gradient scanner-submit-btn" disabled={isSubmitDisabled}>
                  {loading ? (
                    <>
                      <span className="spinner"></span>
                      Scanning Document...
                    </>
                  ) : (
                    <>
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="11" cy="11" r="8"/>
                        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                      </svg>
                      Execute Plagiarism Scan
                    </>
                  )}
                </button>
              </div>
            </form>

            {error && (
              <div className="error-banner">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="12" y1="8" x2="12" y2="12"/>
                  <line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                {error}
              </div>
            )}
          </section>
        )}

        {/* 5. PLAGIARISM & AI DETECTION REPORT DASHBOARD */}
        {token && report && (
          <section className="results-section">
            <div className="results-header">
              <div>
                <h2>Plagiarism & Integrity Report</h2>
                <div className="results-subtitle">
                  Chunk-by-chunk breakdown across exact match, pgvector semantic similarity, and AI detection.
                </div>
              </div>
            </div>

            {/* KPI METRIC CARDS */}
            <div className="kpi-grid">
              <div className="kpi-card">
                <span className="kpi-title">Max Similarity</span>
                <span className="kpi-value" style={{ color: maxSimilarityScore > 70 ? '#b91c1c' : maxSimilarityScore > 40 ? '#b45309' : '#15803d' }}>
                  {maxSimilarityScore.toFixed(1)}%
                </span>
                <span className="kpi-desc">Highest detected chunk match</span>
              </div>

              <div className="kpi-card">
                <span className="kpi-title">Severity Level</span>
                <span className="kpi-value">
                  {exactMatchCount > 0 ? (
                    <span className="status-badge badge-exact">EXACT MATCH</span>
                  ) : semanticMatchCount > 0 ? (
                    <span className="status-badge badge-semantic">SEMANTIC MATCH</span>
                  ) : (
                    <span className="status-badge badge-none">CLEAN</span>
                  )}
                </span>
                <span className="kpi-desc">{exactMatchCount} exact, {semanticMatchCount} semantic</span>
              </div>

              <div className="kpi-card">
                <span className="kpi-title">AI Content Likelihood</span>
                <span className="kpi-value">
                  {aiFlaggedCount > 0 ? (
                    <span className="status-badge badge-ai">{aiFlaggedCount} Flagged</span>
                  ) : (
                    <span className="status-badge badge-human">Human Verified</span>
                  )}
                </span>
                <span className="kpi-desc">Probabilistic signal (RAID calibrated)</span>
              </div>

              <div className="kpi-card">
                <span className="kpi-title">Total Chunks</span>
                <span className="kpi-value">{report.length}</span>
                <span className="kpi-desc">Indexed segments analyzed</span>
              </div>
            </div>

            {/* REPORT TABLE */}
            <div className="table-wrapper">
              <table className="report-table">
                <thead>
                  <tr>
                    <th className="col-idx">#</th>
                    <th className="col-text">Text Excerpt</th>
                    <th className="col-type">Match Type</th>
                    <th className="col-score">Similarity</th>
                    <th className="col-ai">AI Detection</th>
                    <th className="col-tags">Topic Tags</th>
                    <th className="col-summary">Source Summary</th>
                  </tr>
                </thead>
                <tbody>
                  {report.map((chunk, index) => {
                    const matchType = chunk.match_type || 'none';
                    
                    // Extract best score
                    let scoreText = '-';
                    let scoreClass = 'score-low';
                    if (chunk.semantic_matches && chunk.semantic_matches.length > 0) {
                      const sim = chunk.semantic_matches[0].similarity * 100;
                      scoreText = sim.toFixed(1) + '%';
                      scoreClass = sim >= 70 ? 'score-high' : sim >= 50 ? 'score-medium' : 'score-low';
                    } else if (matchType === 'exact') {
                      scoreText = '100%';
                      scoreClass = 'score-high';
                    }

                    const aiDetection = chunk.ai_detection;

                    return (
                      <tr key={index}>
                        <td className="col-idx">{index + 1}</td>
                        <td className="col-text">
                          <div className="text-snippet-box" title={chunk.text}>
                            {chunk.text.length > 80 ? chunk.text.substring(0, 80) + '...' : chunk.text}
                          </div>
                        </td>
                        <td className="col-type">
                          <span className={`status-badge badge-${matchType}`}>
                            {matchType.toUpperCase()}
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
                              title="Probabilistic AI classification signal. Non-binary signal with known false-positive rates."
                            >
                              {aiDetection.formatted}
                            </span>
                          ) : (
                            <span style={{ color: '#94a3b8' }}>-</span>
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
                            <span style={{ color: '#94a3b8' }}>-</span>
                          )}
                        </td>
                        <td className="col-summary">
                          <div className="summary-text-block">
                            {chunk.source_summary || <span style={{ color: '#94a3b8' }}>No source summary available</span>}
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </main>
    </div>
  )
}

export default App
