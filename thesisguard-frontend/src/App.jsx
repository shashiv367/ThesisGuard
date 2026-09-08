import './App.css'
import { useAuth } from './hooks/useAuth'
import { useScanner } from './hooks/useScanner'
import { Navbar } from './components/layout/Navbar'
import { HeroSection } from './components/layout/HeroSection'
import { AuthCard } from './components/auth/AuthCard'
import { ScannerCard } from './components/scanner/ScannerCard'
import { ResultsDashboard } from './components/dashboard/ResultsDashboard'

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
  const auth = useAuth()
  const scanner = useScanner(auth.token, auth.handleLogout)

  return (
    <div className="app-wrapper">
      {/* 1. TOP NAVIGATION BAR */}
      <Navbar 
        token={auth.token} 
        currentUser={auth.currentUser} 
        handleLogout={auth.handleLogout} 
      />

      {/* 2. MAIN APPLICATION WORKSPACE */}
      <main className="app-main">
        {/* HERO SECTION */}
        <HeroSection />

        {/* 3. AUTHENTICATION (Login / Signup) */}
        {!auth.token ? (
          <AuthCard auth={auth} />
        ) : (
          /* 4. SCANNER CARD (Upload File vs Paste Text) */
          <ScannerCard scanner={scanner} />
        )}

        {/* 5. PLAGIARISM & AI DETECTION REPORT DASHBOARD */}
        {auth.token && scanner.report && (
          <ResultsDashboard report={scanner.report} metrics={scanner.metrics} />
        )}
      </main>
    </div>
  )
}

export default App
