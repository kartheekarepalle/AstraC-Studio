import React from 'react'

export default function ErrorConsole({ errors = [] }) {
  if (!errors || errors.length === 0) return null
  // Errors are now shown inside OutputTabs → Errors tab — this component is kept for compatibility
  return null
}
