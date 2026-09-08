export function Navbar({ token, currentUser, handleLogout }) {
  return (
    <nav className="app-navbar">
      <div className="navbar-inner">
        <div className="brand-group">
          {/* Shield / integrity icon */}
          <div className="brand-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
          </div>
          <div className="brand-name">Thesis<span>Guard</span></div>
          <span className="brand-badge">Beta</span>
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
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                <polyline points="16 17 21 12 16 7"/>
                <line x1="21" y1="12" x2="9" y2="12"/>
              </svg>
              Sign out
            </button>
          </div>
        ) : (
          <div className="user-profile-bar" />
        )}
      </div>
    </nav>
  )
}
