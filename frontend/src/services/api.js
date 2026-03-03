export async function compileAndRun(source, mode = 'auto', stdin = '') {
  const resp = await fetch('/api/compile-run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source, mode, stdin })
  })
  if (!resp.ok) {
    const txt = await resp.text()
    throw new Error(`Server error: ${resp.status} ${txt}`)
  }
  const data = await resp.json()
  return data
}

export async function getHealth() {
  const resp = await fetch('/api/health')
  if (!resp.ok) {
    return { ok: false }
  }
  try {
    return await resp.json()
  } catch (e) {
    return { ok: false }
  }
}
