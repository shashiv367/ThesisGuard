import { useState, useMemo } from 'react'
import { uploadDocument, checkText } from '../services/scannerService'

export function useScanner(token, handleLogout) {
  const [mode, setMode] = useState('upload') // 'upload' | 'text'
  const [file, setFile] = useState(null)
  const [pastedText, setPastedText] = useState('')
  const [title, setTitle] = useState('')
  const [loading, setLoading] = useState(false)
  const [report, setReport] = useState(null)
  const [error, setError] = useState(null)

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
      let data
      if (mode === 'upload') {
        data = await uploadDocument(file, token)
      } else {
        data = await checkText(pastedText, title, token)
      }
      setReport(data.report)
    } catch (err) {
      if (err.message.includes('session has expired')) {
        handleLogout()
      }
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const isSubmitDisabled = loading || (mode === 'upload' ? !file : !pastedText.trim())

  const clearReport = () => {
    setReport(null)
    setError(null)
  }

  const metrics = useMemo(() => {
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
    
    return {
      maxSimilarityScore,
      exactMatchCount,
      semanticMatchCount,
      aiFlaggedCount
    }
  }, [report])

  return {
    mode,
    setMode,
    file,
    pastedText,
    setPastedText,
    title,
    setTitle,
    loading,
    report,
    error,
    setError,
    handleFileChange,
    handleRemoveFile,
    handleSubmit,
    isSubmitDisabled,
    clearReport,
    metrics
  }
}
