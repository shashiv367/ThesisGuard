export const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'

export const handleApiError = async (response) => {
  if (response.status === 401) {
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
