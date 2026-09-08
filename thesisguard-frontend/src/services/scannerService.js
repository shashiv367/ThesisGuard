import { baseUrl, handleApiError } from './api'

export const uploadDocument = async (file, token) => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${baseUrl}/upload`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData,
  })

  if (!response.ok) {
    await handleApiError(response)
  }

  return response.json()
}

export const checkText = async (text, title, token) => {
  const response = await fetch(`${baseUrl}/check-text`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      text,
      title: title.trim() || undefined,
    }),
  })

  if (!response.ok) {
    await handleApiError(response)
  }

  return response.json()
}
