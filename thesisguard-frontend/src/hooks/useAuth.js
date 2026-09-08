import { useState, useCallback } from 'react'
import { login, signup } from '../services/authService'

export function useAuth() {
  const [token, setToken] = useState(() => localStorage.getItem('thesisguard_token'))
  const [currentUser, setCurrentUser] = useState(() => {
    const saved = localStorage.getItem('thesisguard_user')
    return saved ? JSON.parse(saved) : null
  })
  
  const [authMode, setAuthMode] = useState('login')
  const [authEmail, setAuthEmail] = useState('')
  const [authPassword, setAuthPassword] = useState('')
  const [authError, setAuthError] = useState(null)
  const [authLoading, setAuthLoading] = useState(false)

  const handleLogout = useCallback(() => {
    setToken(null)
    setCurrentUser(null)
    localStorage.removeItem('thesisguard_token')
    localStorage.removeItem('thesisguard_user')
  }, [])

  const handleAuthSubmit = async (e) => {
    e.preventDefault()
    setAuthError(null)
    setAuthLoading(true)

    try {
      const data = authMode === 'signup' 
        ? await signup(authEmail, authPassword)
        : await login(authEmail, authPassword)

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

  return {
    token,
    currentUser,
    authMode,
    setAuthMode,
    authEmail,
    setAuthEmail,
    authPassword,
    setAuthPassword,
    authError,
    setAuthError,
    authLoading,
    handleLogout,
    handleAuthSubmit
  }
}
