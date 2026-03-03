import React, { useState, useCallback, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  LayoutGrid, Type, Zap, BarChart3, FileCode2, Terminal, AlertCircle,
  Copy, Check, Variable, TriangleAlert, GitBranch
} from 'lucide-react'
import SyntaxTree from './SyntaxTree'

/* ── Tab definitions ───────────────────────────────────────────────── */
const TABS = [
  { key: 'tokens',            label: 'Tokens',       Icon: LayoutGrid },
  { key: 'ast',               label: 'Syntax Tree',  Icon: GitBranch },
  { key: 'symbol_table',      label: 'Symbols',      Icon: Type },
  { key: 'intermediate_code', label: 'IR',            Icon: Zap },
  { key: 'optimized_code',    label: 'Optimized',     Icon: BarChart3 },
  { key: 'assembly',          label: 'Assembly',      Icon: FileCode2 },
  { key: 'runtime',           label: 'Output',        Icon: Terminal },
  { key: 'errors',            label: 'Errors',        Icon: AlertCircle },
]

/* ── Fade-up animation variant ─────────────────────────────────────── */
const fadeUp = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  exit:    { opacity: 0, y: -8 },
  transition: { duration: 0.25, ease: [0.25, 0.46, 0.45, 0.94] },
}

function getTokenClass(type) {
  const t = (type || '').toLowerCase()
  if (t === 'keyword') return 'token-keyword'
  if (t === 'id') return 'token-id'
  if (t === 'number') return 'token-number'
  if (t === 'op' || t === 'assign') return 'token-op'
  if (t === 'string') return 'token-string'
  if (t === 'semicolon' || t === 'comma') return 'token-semicolon'
  if (t.includes('paren') || t.includes('brace') || t.includes('brack')) return 'token-lparen'
  return 'token-default'
}

export default function OutputTabs({ analysis, runtime, errors }) {
  const [active, setActive] = useState('tokens')
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (runtime && (runtime.stdout || runtime.stderr || runtime.exit_code !== undefined)) {
      setActive('runtime')
    }
  }, [runtime])

  const getCount = (key) => {
    if (key === 'tokens') return analysis?.tokens?.length || 0
    if (key === 'ast') return analysis?.ast ? 1 : 0
    if (key === 'symbol_table') return analysis?.symbol_table?.length || 0
    if (key === 'intermediate_code') return analysis?.intermediate_code?.length || 0
    if (key === 'optimized_code') return analysis?.optimized_code?.length || 0
    if (key === 'assembly') return analysis?.assembly?.length || 0
    if (key === 'errors') return (errors?.length || 0) + (analysis?.errors?.length || 0)
    return 0
  }

  const isTabDisabled = (key) => {
    if (!analysis) return false
    if (key === 'ast') return !analysis.ast
    if (key === 'assembly') return !analysis.assembly?.length
    return false
  }

  const getText = useCallback(() => {
    if (active === 'tokens') return (analysis?.tokens || []).map(t => `${t.type}\t${t.value}`).join('\n')
    if (active === 'ast') return JSON.stringify(analysis?.ast, null, 2)
    if (active === 'symbol_table') return (analysis?.symbol_table || []).join('\n')
    if (active === 'intermediate_code') return (analysis?.intermediate_code || []).join('\n')
    if (active === 'optimized_code') return (analysis?.optimized_code || []).join('\n')
    if (active === 'assembly') return (analysis?.assembly || []).join('\n')
    if (active === 'runtime') return `stdout:\n${runtime?.stdout || ''}\n\nstderr:\n${runtime?.stderr || ''}`
    if (active === 'errors') return [...(analysis?.errors || []), ...(errors || [])].join('\n')
    return ''
  }, [active, analysis, runtime, errors])

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(getText())
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {}
  }

  const hasData = analysis || runtime

  return (
    <div className="flex flex-col flex-1 min-h-0">
      {/* ── Tab Bar ──────────────────────────────────────────────── */}
      <div className="flex items-center gap-0.5 border-b border-[var(--t-border)] overflow-x-auto custom-scrollbar" role="tablist" style={{ padding: '10px 16px' }}>
        {TABS.map(tab => {
          const count = getCount(tab.key)
          const isActive = active === tab.key
          const disabled = isTabDisabled(tab.key)
          const Icon = tab.Icon
          return (
            <button
              key={tab.key}
              role="tab"
              aria-selected={isActive}
              onClick={() => !disabled && setActive(tab.key)}
              className={`tab-btn ${isActive ? 'active' : ''} ${disabled ? 'disabled' : ''}`}
            >
              <Icon size={14} style={{ color: isActive ? '#6366F1' : '#8B92A5' }} />
              {tab.label}
              {count > 0 && (
                <span className="tab-count-badge">{count}</span>
              )}
              {isActive && (
                <motion.div
                  layoutId="activeTab"
                  className="tab-active-bar"
                  transition={{ type: 'spring', stiffness: 500, damping: 35 }}
                />
              )}
            </button>
          )
        })}
      </div>

      {/* ── Content header with copy ─────────────────────────────── */}
      {active !== 'ast' && (
        <div className="flex items-center justify-between border-b border-[var(--t-border)]" style={{ padding: '10px 20px', opacity: 0.85 }}>
          <span className="text-[0.7rem] font-semibold tracking-wider uppercase" style={{ color: 'var(--t-text-dim)' }}>
            {TABS.find(t => t.key === active)?.label}
          </span>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleCopy}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[0.65rem] font-medium transition-all cursor-pointer ${
              copied
                ? 'bg-[rgba(16,185,129,0.08)] text-[#10B981] border border-[rgba(16,185,129,0.15)]'
                : 'hover:bg-[var(--t-glass-hover)] border border-transparent'
            }`}
            style={{ color: copied ? undefined : 'var(--t-text-dim)' }}
          >
            {copied ? <Check size={11} /> : <Copy size={11} />}
            {copied ? 'Copied!' : 'Copy'}
          </motion.button>
        </div>
      )}

      {/* ── Content area ─────────────────────────────────────────── */}
      <div className="flex-1 min-h-0 overflow-auto custom-scrollbar">
        <AnimatePresence mode="wait">
          <motion.div
            key={active}
            {...fadeUp}
            className={active === 'ast' ? 'h-full' : ''}
            style={active !== 'ast' ? { padding: '20px' } : undefined}
          >
            {!hasData ? (
              <EmptyState />
            ) : (
              <>
                {active === 'tokens' && <TokensView tokens={analysis?.tokens || []} />}
                {active === 'ast' && <SyntaxTree ast={analysis?.ast} />}
                {active === 'symbol_table' && <SymbolsView symbols={analysis?.symbol_table || []} />}
                {active === 'intermediate_code' && <CodeView lines={analysis?.intermediate_code || []} />}
                {active === 'optimized_code' && <CodeView lines={analysis?.optimized_code || []} />}
                {active === 'assembly' && <CodeView lines={analysis?.assembly || []} />}
                {active === 'runtime' && <RuntimeView runtime={runtime} />}
                {active === 'errors' && <ErrorsView errors={[...(analysis?.errors || []), ...(errors || [])]} />}
              </>
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  )
}

/* ═══════════════════════════════════════════════════════════════════════
   SUB-VIEWS
   ═══════════════════════════════════════════════════════════════════════ */

function EmptyState() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4 }}
      className="flex flex-col items-center justify-center py-20 text-center"
    >
      <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-5"
        style={{
          background: 'var(--t-accent-subtle)',
          border: '1px solid var(--t-border)',
          boxShadow: 'var(--t-shadow-sm)'
        }}>
        <Terminal size={28} style={{ color: 'var(--t-text-dim)', opacity: 0.5 }} />
      </div>
      <p className="text-sm max-w-xs leading-relaxed" style={{ color: 'var(--t-text-dim)' }}>
        Write some C code and hit <strong style={{ color: 'var(--t-text)', fontWeight: 600 }}>Run</strong> to see all compiler phases visualized here.
      </p>
      <span className="mt-3 text-[0.65rem] font-mono px-2.5 py-1 rounded-md"
        style={{ color: 'var(--t-text-dim)', background: 'var(--t-code-bg)', border: '1px solid var(--t-border)' }}>
        Ctrl + Enter
      </span>
    </motion.div>
  )
}

function TokensView({ tokens }) {
  if (!tokens.length) return <EmptySection text="No tokens generated" />
  return (
    <table className="tokens-table-premium">
      <thead>
        <tr>
          <th>#</th>
          <th>Type</th>
          <th>Value</th>
        </tr>
      </thead>
      <tbody>
        {tokens.map((t, i) => (
          <motion.tr
            key={i}
            initial={{ opacity: 0, x: -6 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: Math.min(i * 0.01, 0.3), duration: 0.15 }}
          >
            <td>{i + 1}</td>
            <td>
              <span className={`token-badge ${getTokenClass(t.type)}`}>{t.type}</span>
            </td>
            <td>{t.value}</td>
          </motion.tr>
        ))}
      </tbody>
    </table>
  )
}

function SymbolsView({ symbols }) {
  if (!symbols.length) return <EmptySection text="No symbols found" />
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
      {symbols.map((s, i) => {
        const parts = typeof s === 'string' ? s.split(':') : [s, '']
        const name = parts[0]?.trim()
        const type = parts[1]?.trim() || ''
        return (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.04, ease: [0.25, 0.46, 0.45, 0.94] }}
            className="symbol-card-premium"
          >
            <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
              style={{ background: 'var(--t-accent-subtle)' }}>
              <Variable size={14} style={{ color: '#6366F1' }} />
            </div>
            <div className="min-w-0">
              <div className="text-sm font-semibold truncate font-mono" style={{ color: 'var(--t-text)' }}>{name}</div>
              {type && <div className="text-[0.65rem] truncate" style={{ color: 'var(--t-text-dim)' }}>{type}</div>}
            </div>
          </motion.div>
        )
      })}
    </div>
  )
}

function CodeView({ lines }) {
  if (!lines.length) return <EmptySection text="No output" />
  return (
    <div className="rounded-lg overflow-hidden" style={{ background: 'var(--t-code-bg)', border: '1px solid var(--t-border)' }}>
      <div className="p-3">
        {lines.map((line, i) => (
          <div className="code-line-numbered" key={i}>
            <span className="code-line-num">{i + 1}</span>
            <span className="code-line-text">{line}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function RuntimeView({ runtime }) {
  const stdout = runtime?.stdout || ''
  const stderr = runtime?.stderr || ''
  const exitCode = runtime?.exit_code ?? runtime?.returncode ?? null
  const elapsed = runtime?.execution_time_ms ?? runtime?.elapsed_ms ?? null

  return (
    <div className="flex flex-col gap-4">
      {/* stdout */}
      <motion.div {...fadeUp}>
        <div className="flex items-center gap-2 mb-2">
          <Terminal size={13} style={{ color: '#10B981' }} />
          <span className="text-[0.7rem] font-semibold tracking-wider uppercase" style={{ color: 'var(--t-text-secondary)' }}>Standard Output</span>
        </div>
        <div className={`runtime-stdout ${!stdout ? 'italic' : ''}`} style={!stdout ? { color: 'var(--t-text-dim)' } : undefined}>
          {stdout || '(no output)'}
        </div>
      </motion.div>

      {/* stderr */}
      {stderr && (
        <motion.div {...fadeUp} transition={{ ...fadeUp.transition, delay: 0.1 }}>
          <div className="flex items-center gap-2 mb-2">
            <TriangleAlert size={13} style={{ color: '#EF4444' }} />
            <span className="text-[0.7rem] font-semibold tracking-wider uppercase" style={{ color: '#EF4444', opacity: 0.8 }}>Standard Error</span>
          </div>
          <div className="runtime-stderr">{stderr}</div>
        </motion.div>
      )}

      {/* Footer badges */}
      <motion.div {...fadeUp} transition={{ ...fadeUp.transition, delay: 0.15 }} className="flex items-center gap-2 pt-2">
        {exitCode !== null && (
          <span className={`inline-flex items-center gap-1.5 text-[0.65rem] font-bold px-2.5 py-1 rounded-md font-mono ${
            exitCode === 0
              ? 'bg-[rgba(16,185,129,0.08)] text-[#10B981] border border-[rgba(16,185,129,0.12)]'
              : 'bg-[rgba(239,68,68,0.08)] text-[#EF4444] border border-[rgba(239,68,68,0.12)]'
          }`}>
            {exitCode === 0 ? <Check size={10} /> : <AlertCircle size={10} />}
            Exit: {exitCode}
          </span>
        )}
        {elapsed !== null && (
          <span className="inline-flex items-center gap-1 text-[0.65rem] font-bold px-2.5 py-1 rounded-md font-mono"
            style={{ background: 'var(--t-badge-bg)', color: 'var(--t-accent-light)' }}>
            <Zap size={10} />
            {elapsed} ms
          </span>
        )}
      </motion.div>
    </div>
  )
}

function ErrorsView({ errors }) {
  if (!errors.length) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex flex-col items-center justify-center py-16 text-center"
      >
        <div className="w-12 h-12 rounded-xl bg-[rgba(16,185,129,0.08)] border border-[rgba(16,185,129,0.12)] flex items-center justify-center mb-4"
          style={{ boxShadow: '0 2px 8px rgba(16, 185, 129, 0.06)' }}>
          <Check size={20} style={{ color: '#10B981' }} />
        </div>
        <p className="text-sm" style={{ color: 'var(--t-text-dim)' }}>No errors — looking good!</p>
      </motion.div>
    )
  }
  return (
    <div className="flex flex-col gap-2.5">
      {errors.map((e, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0, x: -12 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.06, ease: [0.25, 0.46, 0.45, 0.94] }}
          className="error-item-card"
        >
          <AlertCircle size={14} className="flex-shrink-0 mt-0.5" />
          <div className="min-w-0 break-words">{typeof e === 'string' ? e : JSON.stringify(e)}</div>
        </motion.div>
      ))}
    </div>
  )
}

function EmptySection({ text }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <p className="text-sm" style={{ color: 'var(--t-text-dim)' }}>{text}</p>
    </div>
  )
}
