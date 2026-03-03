import React, { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Play, Terminal, Cpu, ChevronDown, ChevronRight,
  Zap, CheckCircle2, XCircle, Loader2, Sun, Moon, Braces
} from 'lucide-react'
import Editor from './components/Editor'
import OutputTabs from './components/OutputTabs'
import Spinner from './components/Spinner'
import HealthBanner from './components/HealthBanner'
import { compileAndRun, getHealth } from './services/api'

const SAMPLE = `#include <stdio.h>

int main() {
    int a = 5;
    int b = 10;
    int sum = a + b;
    printf("Sum = %d\\n", sum);
    return 0;
}
`

/* ── Theme helpers ───────────────────────────────────────────────────── */
function getInitialTheme() {
  try {
    const saved = localStorage.getItem('astrac-theme')
    if (saved === 'light' || saved === 'dark') return saved
  } catch {}
  return 'dark'
}

function applyTheme(t) {
  document.documentElement.setAttribute('data-theme', t)
  try { localStorage.setItem('astrac-theme', t) } catch {}
}

/* ── Status config ───────────────────────────────────────────────────── */
const STATUS_CFG = {
  idle:      { label: 'Ready',     dot: 'bg-[#8B92A5]',  icon: Terminal },
  compiling: { label: 'Compiling', dot: 'bg-[#6366F1]',  icon: Loader2 },
  success:   { label: 'Success',   dot: 'bg-[#10B981]',  icon: CheckCircle2 },
  error:     { label: 'Error',     dot: 'bg-[#EF4444]',  icon: XCircle },
}

export default function App() {
  const [source, setSource] = useState(SAMPLE)
  const [analysis, setAnalysis] = useState(null)
  const [runtime, setRuntime] = useState(null)
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState('idle')
  const [errors, setErrors] = useState([])
  const [markers, setMarkers] = useState([])
  const [useLocal, setUseLocal] = useState(true)
  const [health, setHealth] = useState(null)
  const [healthDismissed, setHealthDismissed] = useState(false)
  const [theme, setTheme] = useState(getInitialTheme)
  const [stdinInput, setStdinInput] = useState('')
  const [showStdin, setShowStdin] = useState(false)

  useEffect(() => {
    const needsInput = /\b(scanf|gets|getchar|fgets|fgetc|getc)\s*\(/.test(source)
    if (needsInput && !showStdin) setShowStdin(true)
  }, [source])

  useEffect(() => { applyTheme(theme) }, [theme])
  const toggleTheme = useCallback(() => {
    setTheme(t => t === 'dark' ? 'light' : 'dark')
  }, [])

  useEffect(() => {
    let alive = true
    getHealth().then(h => alive && setHealth(h)).catch(() => {})
    return () => { alive = false }
  }, [])

  const compileRef = useRef(null)

  const handleCompile = async () => {
    setLoading(true)
    setStatus('compiling')
    setErrors([])
    setAnalysis(null)
    setRuntime(null)
    setMarkers([])

    try {
      const mode = useLocal ? 'local' : 'auto'
      const res = await compileAndRun(source, mode, stdinInput)

      const raw = res.phases || res.analysis || {}
      setAnalysis({
        tokens:            raw.tokens || [],
        ast:               raw.ast || null,
        symbol_table:      raw.symbols || raw.symbol_table || [],
        intermediate_code: raw.ir || raw.intermediate_code || [],
        optimized_code:    raw.opt_ir || raw.optimized_code || [],
        assembly:          raw.asm || raw.assembly || [],
        errors:            raw.errors || [],
      })

      const r = res.run || res.runtime || { stdout: '', stderr: '', exit_code: 0 }

      if (!r.stdout && !r.stderr && r.exit_code === null) {
        const needsInput = /\b(scanf|gets|getchar|fgets|fgetc|getc)\s*\(/.test(source)
        if (needsInput) {
          r.stderr = 'Program timed out — it needs input via scanf/gets. Open the Stdin panel below the editor and provide the input values.'
          r.exit_code = -1
        }
      }

      setRuntime(r)

      const errs = []
      if (raw.errors?.length) raw.errors.forEach(e => errs.push(typeof e === 'string' ? e : e.message || JSON.stringify(e)))
      if (res.errors?.length) res.errors.forEach(e => errs.push(typeof e === 'string' ? e : e.message || JSON.stringify(e)))
      if (r.stderr && r.exit_code !== 0) errs.push(r.stderr)

      if (errs.length) {
        setErrors(errs)
        setStatus('error')
      } else {
        setStatus('success')
      }
    } catch (err) {
      setStatus('error')
      setErrors([err?.message || String(err)])
    } finally {
      setLoading(false)
    }
  }

  compileRef.current = handleCompile
  useEffect(() => {
    const handler = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault()
        compileRef.current?.()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  const st = STATUS_CFG[status]
  const StatusIcon = st.icon

  return (
    <div className="flex flex-col h-screen overflow-hidden relative">
      {/* ── Layered ambient gradient background ───────────────────── */}
      <div className="bg-layered-gradient" />

      {/* ── Gradient accent line ──────────────────────────────────── */}
      <div className="header-gradient-line" />

      {/* ── Header / Nav Bar ──────────────────────────────────────── */}
      <motion.header
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
        className="header-glass relative z-20 flex items-center justify-between px-6"
        style={{ paddingTop: '14px', paddingBottom: '14px' }}
      >
        {/* Left: Brand */}
        <motion.div
          className="flex items-center gap-3"
          whileHover={{ scale: 1.01 }}
          transition={{ type: 'spring', stiffness: 400, damping: 25 }}
        >
          <div className="logo-icon w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, #6366F1, #8B5CF6)', boxShadow: '0 2px 8px rgba(99, 102, 241, 0.25)' }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 3L4 7.5V16.5L12 21L20 16.5V7.5L12 3Z" stroke="white" strokeWidth="1.5" strokeLinejoin="round" fill="rgba(255,255,255,0.1)" />
              <text x="12" y="16" textAnchor="middle" fill="white" fontFamily="Inter, sans-serif" fontWeight="700" fontSize="11">A</text>
            </svg>
          </div>
          <div className="flex items-center gap-2.5">
            <span className="text-base font-bold tracking-tight brand-glow select-none gradient-text"
              style={{ fontFamily: "'Inter', sans-serif", letterSpacing: '-0.02em' }}>
              AstraC <span style={{ fontWeight: 500, opacity: 0.7 }}>Studio</span>
            </span>
            <span className="text-[0.55rem] font-semibold tracking-[0.1em] uppercase px-1.5 py-0.5 rounded font-mono"
              style={{ background: 'var(--t-badge-bg)', color: 'var(--t-accent-light)' }}>
              IDE
            </span>
          </div>
        </motion.div>

        {/* Center: Compile Button */}
        <div className="flex items-center gap-3">
          <motion.button
            whileHover={{ scale: 1.03, y: -1 }}
            whileTap={{ scale: 0.97 }}
            onClick={handleCompile}
            disabled={loading}
            className="compile-btn-premium flex items-center gap-2 px-5 py-2.5 font-semibold text-sm text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            {loading ? (
              <Loader2 size={15} className="animate-spin" />
            ) : (
              <Play size={15} fill="currentColor" />
            )}
            {loading ? 'Compiling…' : 'Run Code'}
          </motion.button>

          <span className="text-[0.65rem] hidden sm:block font-mono"
            style={{ color: 'var(--t-text-dim)' }}>
            Ctrl + Enter
          </span>
        </div>

        {/* Right: Controls */}
        <div className="flex items-center gap-4">
          {/* Pipeline toggle */}
          <label className="flex items-center gap-2 cursor-pointer select-none group">
            <div
              className={`relative w-9 h-5 rounded-full transition-all duration-300 ${
                useLocal
                  ? 'bg-[rgba(99,102,241,0.2)] border border-[rgba(99,102,241,0.3)]'
                  : 'border'
              }`}
              style={!useLocal ? { background: 'var(--t-glass)', borderColor: 'var(--t-border)' } : undefined}
            >
              <motion.div
                layout
                transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                className={`absolute top-0.5 w-4 h-4 rounded-full ${
                  useLocal
                    ? 'left-[18px] bg-[#6366F1]'
                    : 'left-0.5'
                }`}
                style={!useLocal ? { background: 'var(--t-text-dim)' } : { boxShadow: '0 1px 4px rgba(99, 102, 241, 0.3)' }}
              />
            </div>
            <input
              type="checkbox"
              checked={useLocal}
              onChange={e => setUseLocal(e.target.checked)}
              className="sr-only"
            />
            <span className="text-xs transition-colors"
              style={{ color: 'var(--t-text-dim)' }}>
              Local
            </span>
          </label>

          {/* Status badge */}
          <motion.div
            key={status}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex items-center gap-1.5 text-xs font-medium"
            style={{ color: status === 'success' ? '#10B981' : status === 'error' ? '#EF4444' : status === 'compiling' ? '#6366F1' : 'var(--t-text-dim)' }}
          >
            {status === 'compiling' ? (
              <Loader2 size={12} className="animate-spin" />
            ) : (
              <span className={`w-2 h-2 rounded-full ${st.dot} ${status === 'idle' ? '' : 'status-dot-pulse'}`} />
            )}
            {st.label}
          </motion.div>

          {/* Theme toggle */}
          <motion.button
            whileHover={{ scale: 1.1, rotate: 15 }}
            whileTap={{ scale: 0.9 }}
            onClick={toggleTheme}
            className="p-2 rounded-lg transition-colors cursor-pointer"
            style={{ color: '#8B92A5', background: 'var(--t-glass-hover)' }}
            aria-label="Toggle theme"
          >
            <AnimatePresence mode="wait">
              <motion.div
                key={theme}
                initial={{ rotate: -90, opacity: 0 }}
                animate={{ rotate: 0, opacity: 1 }}
                exit={{ rotate: 90, opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
              </motion.div>
            </AnimatePresence>
          </motion.button>
        </div>
      </motion.header>

      <HealthBanner health={health} dismissed={healthDismissed} onDismiss={() => setHealthDismissed(true)} />

      {/* ── Main Split Layout ─────────────────────────────────────── */}
      <main className="flex-1 flex overflow-hidden relative z-10 gap-6" style={{ padding: '18px 28px 14px' }}>
        {/* ── Left: Editor Panel ──────────────────────────────────── */}
        <motion.div
          initial={{ x: -30, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.1, ease: [0.25, 0.46, 0.45, 0.94] }}
          className="flex flex-col w-1/2 min-w-0"
        >
          <div className="flex flex-col rounded-xl overflow-hidden glass-card" style={{ height: '75vh' }}>
            {/* Panel header */}
            <div className="flex items-center justify-between"
              style={{ padding: '14px 20px', borderBottom: '1px solid var(--t-border)' }}>
              <div className="flex items-center gap-2.5">
                <div className="flex gap-1.5 mr-2">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ background: '#EF4444', opacity: 0.6 }} />
                  <span className="w-2.5 h-2.5 rounded-full" style={{ background: '#F59E0B', opacity: 0.6 }} />
                  <span className="w-2.5 h-2.5 rounded-full" style={{ background: '#10B981', opacity: 0.6 }} />
                </div>
                <Braces size={16} style={{ color: '#8B92A5' }} />
                <span className="font-semibold" style={{ color: 'var(--t-text-secondary)', fontSize: '0.82rem' }}>Editor</span>
              </div>
              <span className="text-[0.6rem] font-semibold tracking-widest uppercase px-2 py-0.5 rounded-md font-mono"
                style={{ background: 'var(--t-badge-bg)', color: 'var(--t-accent-light)' }}>
                C
              </span>
            </div>

            {/* Monaco Editor */}
            <div className="flex-1 min-h-0">
              <Editor value={source} onChange={setSource} markers={markers} theme={theme} />
            </div>

            {/* ── Stdin Section ──────────────────────────────────── */}
            <div style={{ marginTop: '12px', borderTop: '1px solid var(--t-border)', paddingTop: '0px' }}>
              <button
                onClick={() => setShowStdin(s => !s)}
                className="flex items-center gap-2 w-full text-xs font-medium transition-colors cursor-pointer"
                style={{ color: 'var(--t-text-dim)', padding: '12px 20px' }}
              >
                <Terminal size={15} style={{ color: '#8B92A5' }} />
                <span>Stdin</span>
                {showStdin ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                {stdinInput && (
                  <span className="ml-auto text-[0.6rem] px-1.5 py-0.5 rounded-md font-mono"
                    style={{ background: 'var(--t-badge-bg)', color: 'var(--t-accent-light)' }}>
                    {stdinInput.split('\n').length} lines
                  </span>
                )}
              </button>
              <AnimatePresence>
                {showStdin && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.25, ease: [0.25, 0.46, 0.45, 0.94] }}
                    className="overflow-hidden"
                  >
                    <div style={{ padding: '0 20px 16px' }}>
                      <textarea
                        className="stdin-textarea"
                        value={stdinInput}
                        onChange={e => setStdinInput(e.target.value)}
                        placeholder="Enter program input here (one value per line)…"
                        rows={3}
                        spellCheck={false}
                      />
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </motion.div>

        {/* ── Right: Output Panel ─────────────────────────────────── */}
        <motion.div
          initial={{ x: 30, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.2, ease: [0.25, 0.46, 0.45, 0.94] }}
          className="flex flex-col w-1/2 min-w-0"
        >
          <div className="flex flex-col rounded-xl overflow-hidden glass-card" style={{ height: '75vh' }}>
            {/* Panel header */}
            <div className="flex items-center justify-between"
              style={{ padding: '14px 20px', borderBottom: '1px solid var(--t-border)' }}>
              <div className="flex items-center gap-2.5">
                <div className="flex gap-1.5 mr-2">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ background: '#EF4444', opacity: 0.6 }} />
                  <span className="w-2.5 h-2.5 rounded-full" style={{ background: '#F59E0B', opacity: 0.6 }} />
                  <span className="w-2.5 h-2.5 rounded-full" style={{ background: '#10B981', opacity: 0.6 }} />
                </div>
                <Cpu size={16} style={{ color: '#8B92A5' }} />
                <span className="font-semibold" style={{ color: 'var(--t-text-secondary)', fontSize: '0.82rem' }}>Output</span>
              </div>
              {analysis && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="flex items-center gap-1.5"
                >
                  <Zap size={11} style={{ color: '#10B981' }} />
                  <span className="text-[0.6rem] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-md font-mono"
                    style={{ background: 'rgba(16, 185, 129, 0.08)', color: '#10B981' }}>
                    {analysis.tokens?.length || 0} tokens
                  </span>
                </motion.div>
              )}
            </div>

            {/* Output tabs */}
            <div className="flex-1 min-h-0 flex flex-col">
              <OutputTabs analysis={analysis} runtime={runtime} errors={errors} />
            </div>
          </div>
        </motion.div>
      </main>

      {/* ── Status Bar ───────────────────────────────────────────── */}
      <div className="status-bar relative z-20">
        <div className="flex items-center gap-3">
          <span>AstraC Studio v1.0</span>
          <span style={{ color: 'var(--t-border-strong)' }}>|</span>
          <span>Pipeline: {useLocal ? 'Local' : 'Remote'}</span>
        </div>
        <div className="flex items-center gap-3">
          <span>{theme === 'dark' ? 'Dark' : 'Light'} Theme</span>
          <span style={{ color: 'var(--t-border-strong)' }}>|</span>
          <span>GCC {health?.ok ? '✓' : '✗'}</span>
        </div>
      </div>

      {/* ── Loading overlay ───────────────────────────────────────── */}
      <AnimatePresence>
        {loading && <Spinner />}
      </AnimatePresence>
    </div>
  )
}
