import { ErrorBanner } from '../common/ErrorBanner'

export function AuthCard({ auth }) {
  const {
    authMode,
    setAuthMode,
    authEmail,
    setAuthEmail,
    authPassword,
    setAuthPassword,
    authError,
    setAuthError,
    authLoading,
    handleAuthSubmit
  } = auth

  return (
    <section className="auth-card">
      <div className="auth-header">
        <h3>
          {authMode === 'login' ? 'Welcome back' : 'Create your account'}
        </h3>
        <p>
          {authMode === 'login'
            ? 'Sign in to access your scan history and reports.'
            : 'It only takes a moment to get started.'}
        </p>
      </div>

      <div className="segmented-control" role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={authMode === 'login'}
          className={`segmented-btn ${authMode === 'login' ? 'segmented-btn-active' : ''}`}
          onClick={() => { setAuthMode('login'); setAuthError(null); }}
        >
          Sign in
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={authMode === 'signup'}
          className={`segmented-btn ${authMode === 'signup' ? 'segmented-btn-active' : ''}`}
          onClick={() => { setAuthMode('signup'); setAuthError(null); }}
        >
          Register
        </button>
      </div>

      <form onSubmit={handleAuthSubmit} className="auth-form-body">
        <div className="form-field">
          <label className="form-label" htmlFor="auth-email">Email address</label>
          <input
            id="auth-email"
            type="email"
            required
            className="form-input"
            placeholder="you@university.edu"
            value={authEmail}
            onChange={(e) => setAuthEmail(e.target.value)}
            disabled={authLoading}
          />
        </div>

        <div className="form-field">
          <label className="form-label" htmlFor="auth-password">Password</label>
          <input
            id="auth-password"
            type="password"
            required
            minLength={6}
            className="form-input"
            placeholder="At least 6 characters"
            value={authPassword}
            onChange={(e) => setAuthPassword(e.target.value)}
            disabled={authLoading}
          />
        </div>

        <button type="submit" className="btn-primary-gradient" disabled={authLoading}>
          {authLoading && <span className="spinner" />}
          {authLoading
            ? 'Please wait…'
            : authMode === 'login'
            ? 'Sign in'
            : 'Create account'}
        </button>
      </form>

      <ErrorBanner error={authError} />
    </section>
  )
}
