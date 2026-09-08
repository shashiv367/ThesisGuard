import { ErrorBanner } from '../common/ErrorBanner'

export function ScannerCard({ scanner }) {
  const {
    mode,
    setMode,
    file,
    pastedText,
    setPastedText,
    title,
    setTitle,
    loading,
    error,
    setError,
    handleFileChange,
    handleRemoveFile,
    handleSubmit,
    isSubmitDisabled
  } = scanner

  return (
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
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            Upload a file
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={mode === 'text'}
            className={`scanner-tab ${mode === 'text' ? 'scanner-tab-active' : ''}`}
            onClick={() => { setMode('text'); setError(null); }}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
            </svg>
            Paste text
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
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/>
                    <path d="M12 12v9"/>
                    <path d="m16 16-4-4-4 4"/>
                  </svg>
                </div>
                <p className="dropzone-title">Drop your document here, or click to browse</p>
                <p className="dropzone-hint">Accepts PDF and Word documents (.pdf, .docx)</p>
              </div>
            ) : (
              <div style={{ textAlign: 'center' }}>
                <div className="selected-file-chip">
                  <span className="file-info-icon">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
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
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
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
              <label className="form-label" htmlFor="doc-title">Document title <span style={{ fontWeight: 400, color: '#9aaabb' }}>(optional)</span></label>
              <input
                id="doc-title"
                type="text"
                className="form-input"
                placeholder="e.g. Chapter 3: Research Methodology"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                disabled={loading}
              />
            </div>

            <div className="form-field">
              <label className="form-label">Your text</label>
              <div className="textarea-wrapper">
                <textarea
                  className="modern-textarea"
                  placeholder="Paste the section of your paper you'd like to check…"
                  value={pastedText}
                  onChange={(e) => setPastedText(e.target.value)}
                  disabled={loading}
                  rows={9}
                />
                <span className="textarea-stats">
                  {pastedText.trim() ? `${pastedText.trim().split(/\s+/).length} words · ` : ''}{pastedText.length} chars
                </span>
              </div>
            </div>
          </div>
        )}

        <div className="scanner-actions">
          <button type="submit" className="btn-primary-gradient scanner-submit-btn" disabled={isSubmitDisabled}>
            {loading ? (
              <>
                <span className="spinner" />
                Analysing your document…
              </>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="11" cy="11" r="8"/>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
                Check for plagiarism
              </>
            )}
          </button>
        </div>
      </form>

      <ErrorBanner error={error} />
    </section>
  )
}
