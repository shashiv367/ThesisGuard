import { baseUrl } from './api'

export const login = async (email, password) => {
  const response = await fetch(`${baseUrl}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  
  const data = await response.json()
  if (!response.ok) {
    throw new Error(data.detail || 'Authentication failed')
  }
  return data
}

export const signup = async (email, password) => {
  const response = await fetch(`${baseUrl}/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  
  const data = await response.json()
  if (!response.ok) {
    throw new Error(data.detail || 'Authentication failed')
  }
  return data
}
