import React, { useState, useCallback, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  LayoutGrid, GitBranch, Variable, Zap, BarChart3, FileCode2,
  Terminal, AlertCircle, Copy, Check, TriangleAlert,
  Info, SkipForward, CheckCircle2, XCircle, Sparkles, BookOpen,
  Cpu, Layers, Search, Shield, Cog, Rocket
} from 'lucide-react'

/* ═══════════════════════════════════════════════════════════════════════
   PHASE DEFINITIONS — Each has a unique bright color, icon, and
   detailed role description explaining what the phase does.
   ═══════════════════════════════════════════════════════════════════════ */

const PHASE_META = {
  lexical: {
    label: 'Lexical Analysis',
    shortLabel: 'Lexical',
    Icon: Search,
    num: 1,
    color: '#A78BFA',        // Vivid purple
    bgColor: 'rgba(167, 139, 250, 0.12)',
    borderColor: 'rgba(167, 139, 250, 0.25)',
    glowColor: 'rgba(167, 139, 250, 0.20)',
    roleTitle: 'Tokenizer / Scanner',
    roleDescription: 'The lexer scans your source code character by character and breaks it into meaningful atomic units called tokens. It identifies keywords (int, return, if), identifiers (variable names), numeric literals, operators (+, -, =), string literals, and punctuation (;, {, }).',
    roleDetails: 'Each token has a type, a value, and the line number where it was found. This is the first step in understanding your code — turning raw text into a structured stream of recognized patterns.',
    whatItProduces: 'A complete token stream — a sequential list of all tokens found in your source code, with type classification and position data.',
  },
  syntax: {
    label: 'Syntax Analysis',
    shortLabel: 'Syntax',
    Icon: GitBranch,
    num: 2,
    color: '#22D3EE',        // Vivid cyan
    bgColor: 'rgba(34, 211, 238, 0.12)',
    borderColor: 'rgba(34, 211, 238, 0.25)',
    glowColor: 'rgba(34, 211, 238, 0.20)',
    roleTitle: 'Parser / AST Builder',
    roleDescription: 'The parser takes the token stream from the lexer and builds an Abstract Syntax Tree (AST). It checks that your code follows the C grammar rules — verifying proper statement structure, expression nesting, function declarations, and block scoping.',
    roleDetails: 'The AST is a tree where each node represents a code construct (e.g., FuncDecl, BinOp, Assign, Return). The tree structure captures how expressions and statements are nested and related to each other.',
    whatItProduces: 'A visual Abstract Syntax Tree showing the hierarchical structure of your program — how functions, statements, expressions, and operators relate to each other.',
  },
  semantic: {
    label: 'Semantic Analysis',
    shortLabel: 'Semantic',
    Icon: Shield,
    num: 3,
    color: '#F472B6',        // Vivid pink
    bgColor: 'rgba(244, 114, 182, 0.12)',
    borderColor: 'rgba(244, 114, 182, 0.25)',
    glowColor: 'rgba(244, 114, 182, 0.20)',
    roleTitle: 'Type Checker & Symbol Resolver',
    roleDescription: 'The semantic analyzer walks the AST and performs meaning-level checks. It builds a symbol table tracking every variable and function declaration, verifies that variables are declared before use, checks type compatibility in assignments and expressions, and validates function call arguments.',
    roleDetails: 'This phase catches errors that are syntactically valid but semantically wrong — like using an undeclared variable, assigning a string to an int, or calling a function with wrong argument types.',
    whatItProduces: 'A Symbol Table (listing all declared variables, their types, scopes, and declaration lines) and a Type-Annotated AST showing data types resolved for every expression node.',
  },
  intermediate: {
    label: 'IR Generation',
    shortLabel: 'IR Code',
    Icon: Layers,
    num: 4,
    color: '#FBBF24',        // Vivid amber
    bgColor: 'rgba(251, 191, 36, 0.12)',
    borderColor: 'rgba(251, 191, 36, 0.25)',
    glowColor: 'rgba(251, 191, 36, 0.20)',
    roleTitle: 'Three-Address Code Generator',
    roleDescription: 'The IR generator translates the high-level AST into Three-Address Code (TAC) — a low-level, platform-independent representation. Each TAC instruction has at most three operands (e.g., t1 = a + b). Complex expressions are broken down into simple steps using temporary variables.',
    roleDetails: 'TAC is a universal intermediate form that makes optimization easier. It bridges the gap between your high-level C code and the low-level machine/assembly code. Labels and GOTO statements handle control flow.',
    whatItProduces: 'A sequence of Three-Address Code instructions — simple, linear operations with temporary variables that represent your program logic in a form ready for optimization.',
  },
  optimization: {
    label: 'Optimization',
    shortLabel: 'Optimizer',
    Icon: Rocket,
    num: 5,
    color: '#34D399',        // Vivid emerald
    bgColor: 'rgba(52, 211, 153, 0.12)',
    borderColor: 'rgba(52, 211, 153, 0.25)',
    glowColor: 'rgba(52, 211, 153, 0.20)',
    roleTitle: 'Code Optimizer',
    roleDescription: 'The optimizer analyzes the Three-Address Code and applies transformations to make it more efficient without changing behavior. It performs constant folding (computing 3+5 → 8 at compile time), constant propagation (replacing variables with known values), dead code elimination (removing unused computations), and strength reduction.',
    roleDetails: 'Each optimization is tracked and shown with the before/after transformation, so you can see exactly what changed and which rule was applied. This makes your compiled program faster and smaller.',
    whatItProduces: 'Optimized TAC with a detailed changelog showing every transformation applied — what was changed, why, and the optimization rule used.',
  },
  codegen: {
    label: 'Code Generation',
    shortLabel: 'CodeGen',
    Icon: Cpu,
    num: 6,
    color: '#FB923C',        // Vivid orange
    bgColor: 'rgba(251, 146, 60, 0.12)',
    borderColor: 'rgba(251, 146, 60, 0.25)',
    glowColor: 'rgba(251, 146, 60, 0.20)',
    roleTitle: 'Assembly Code Generator',
    roleDescription: 'The code generator translates the optimized TAC into pseudo-assembly instructions. It handles register allocation (mapping temporaries to registers), instruction selection (choosing the right assembly operations), and generating the final code that a CPU can execute.',
    roleDetails: 'The output uses a simplified assembly-like syntax with operations like MOV, ADD, SUB, MUL, PUSH, CALL, and RET. This is the final compilation stage before a real assembler would produce machine code.',
    whatItProduces: 'Pseudo-assembly code with register assignments, stack operations, function calls, and control flow — the lowest-level representation of your program.',
  },
}

const PHASE_TABS = Object.entries(PHASE_META).map(([key, m]) => ({
  key, label: m.shortLabel, Icon: m.Icon, num: m.num, color: m.color
}))

const OUTPUT_TAB = { key: 'runtime', label: 'Output', Icon: Terminal }

/* ── Smooth animation variants ─────────────────────────────────────── */
const fadeUp = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0 },
  exit:    { opacity: 0, y: -10 },
  transition: { duration: 0.3, ease: [0.25, 0.46, 0.45, 0.94] },
}

const cardPop = {
  initial: { opacity: 0, y: 20, scale: 0.96 },
  animate: { opacity: 1, y: 0, scale: 1 },
  transition: { duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] },
}

function getTokenClass(type) {
  const t = (type || '').toLowerCase()
  if (t === 'keyword') return 'token-keyword'
  if (t === 'id') return 'token-id'
  if (t === 'number') return 'token-number'
  if (t === 'op' || t === 'assign' || t === 'multi_op') return 'token-op'
  if (t === 'string') return 'token-string'
  if (t === 'semicolon' || t === 'comma') return 'token-semicolon'
  if (t.includes('paren') || t.includes('brace') || t.includes('brack')) return 'token-lparen'
  return 'token-default'
}


/* ═══════════════════════════════════════════════════════════════════════
   MAIN COMPONENT
   ═══════════════════════════════════════════════════════════════════════ */

export default function OutputTabs({ phases, pipeline, runtime, errors }) {
  const [active, setActive] = useState('lexical')
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (runtime && (runtime.stdout || runtime.stderr || runtime.exit_code !== undefined)) {
      setActive('runtime')
    }
  }, [runtime])

  const getPhase = (id) => {
    if (!phases || !Array.isArray(phases)) return null
    return phases.find(p => p.id === id)
  }

  const getPhaseStatus = (id) => {
    const p = getPhase(id)
    if (!p) return 'pending'
    if (p.skipped) return 'skipped'
    if (p.errors?.length > 0) return 'error'
    if (p.completed) return 'success'
    return 'pending'
  }

  const getErrorCount = (id) => {
    const p = getPhase(id)
    return p?.errors?.length || 0
  }

  const getText = useCallback(() => {
    if (active === 'runtime') {
      return `stdout:\n${runtime?.stdout || ''}\n\nstderr:\n${runtime?.stderr || ''}`
    }
    const p = getPhase(active)
    if (!p?.output) return ''
    const o = p.output
    if (o.tokens) return o.tokens.map(t => `${t.type}\t${t.value}`).join('\n')
    if (o.syntax_tree_ascii) return o.syntax_tree_ascii
    if (o.syntax_tree) return JSON.stringify(o.syntax_tree, null, 2)
    if (o.symbol_table) return o.symbol_table.map(s => `${s.name}: ${s.type} (${s.kind})`).join('\n')
    if (o.semantic_tree_ascii) return o.semantic_tree_ascii
    if (o.tac) return o.tac.join('\n')
    if (o.optimized_tac) return o.optimized_tac.join('\n')
    if (o.assembly) return o.assembly.join('\n')
    return ''
  }, [active, phases, runtime])

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(getText())
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {}
  }

  const hasData = phases?.length > 0 || runtime
  const meta = PHASE_META[active]

  return (
    <div className="flex flex-col flex-1 min-h-0">
      {/* ── Phase Tab Bar ────────────────────────────────────────── */}
      <div className="flex items-center gap-1 border-b border-[var(--t-border)] overflow-x-auto custom-scrollbar"
           role="tablist" style={{ padding: '10px 16px' }}>
        {PHASE_TABS.map(tab => {
          const isActive = active === tab.key
          const status = getPhaseStatus(tab.key)
          const errCount = getErrorCount(tab.key)
          const Icon = tab.Icon
          return (
            <button
              key={tab.key}
              role="tab"
              aria-selected={isActive}
              onClick={() => setActive(tab.key)}
              className={`tab-btn ${isActive ? 'active' : ''} ${status === 'skipped' ? 'disabled' : ''}`}
              style={isActive ? { color: tab.color, background: `${tab.color}15`, borderColor: `${tab.color}30` } : undefined}
            >
              <span className="phase-num">{tab.num}</span>
              <Icon size={13} style={{ color: isActive ? tab.color : status === 'error' ? '#F87171' : '#64748B' }} />
              {tab.label}
              {status === 'error' && errCount > 0 && (
                <span className="tab-error-badge">{errCount}</span>
              )}
              {status === 'success' && (
                <CheckCircle2 size={10} style={{ color: '#34D399' }} />
              )}
              {status === 'skipped' && (
                <SkipForward size={10} style={{ color: '#64748B', opacity: 0.5 }} />
              )}
              {isActive && (
                <motion.div
                  layoutId="activeTab"
                  className="tab-active-bar"
                  style={{ background: `linear-gradient(90deg, ${tab.color}, ${tab.color}80)` }}
                  transition={{ type: 'spring', stiffness: 500, damping: 35 }}
                />
              )}
            </button>
          )
        })}

        {/* Separator */}
        <div style={{ width: 1, height: 20, background: 'var(--t-border-vivid)', margin: '0 8px', flexShrink: 0 }} />

        {/* Output tab */}
        <button
          role="tab"
          aria-selected={active === 'runtime'}
          onClick={() => setActive('runtime')}
          className={`tab-btn ${active === 'runtime' ? 'active' : ''}`}
          style={active === 'runtime' ? { color: '#34D399', background: 'rgba(52,211,153,0.12)', borderColor: 'rgba(52,211,153,0.25)' } : undefined}
        >
          <Terminal size={13} style={{ color: active === 'runtime' ? '#34D399' : '#64748B' }} />
          {OUTPUT_TAB.label}
          {active === 'runtime' && (
            <motion.div
              layoutId="activeTab"
              className="tab-active-bar"
              style={{ background: 'linear-gradient(90deg, #34D399, #22D3EE)' }}
              transition={{ type: 'spring', stiffness: 500, damping: 35 }}
            />
          )}
        </button>
      </div>

      {/* ── Content header with copy ─────────────────────────────── */}
      <div className="flex items-center justify-between border-b border-[var(--t-border)]"
           style={{ padding: '12px 20px' }}>
        <div className="flex items-center gap-2.5">
          {meta && (
            <span className="w-3.5 h-3.5 rounded-full" style={{ background: meta.color, boxShadow: `0 0 12px ${meta.glowColor}` }} />
          )}
          <span className="text-sm font-bold tracking-wider uppercase"
                style={{ color: meta?.color || '#34D399' }}>
            {active === 'runtime'
              ? 'Program Output'
              : meta?.label || active}
          </span>
        </div>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={handleCopy}
          className={`flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
            copied
              ? 'bg-[rgba(52,211,153,0.10)] text-[#34D399] border border-[rgba(52,211,153,0.20)]'
              : 'hover:bg-[var(--t-glass-hover)] border border-transparent'
          }`}
          style={{ color: copied ? undefined : 'var(--t-text-dim)' }}
        >
          {copied ? <Check size={11} /> : <Copy size={11} />}
          {copied ? 'Copied!' : 'Copy'}
        </motion.button>
      </div>

      {/* ── Content area ─────────────────────────────────────────── */}
      <div className="flex-1 min-h-0 overflow-auto custom-scrollbar">
        <AnimatePresence mode="wait">
          <motion.div key={active} {...fadeUp} style={{ padding: '20px' }}>
            {!hasData ? (
              <EmptyState />
            ) : active === 'runtime' ? (
              <RuntimeView runtime={runtime} />
            ) : (
              <PhaseView phase={getPhase(active)} meta={meta} />
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  )
}


/* ═══════════════════════════════════════════════════════════════════════
   PHASE VIEW — Rich card with detailed role description
   ═══════════════════════════════════════════════════════════════════════ */

function PhaseView({ phase, meta }) {
  if (!phase) return <EmptyState />

  if (phase.skipped) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.4, type: 'spring' }}
          className="w-16 h-16 rounded-2xl flex items-center justify-center mb-5"
          style={{ background: 'var(--t-glass-hover)', border: '1px solid var(--t-border-vivid)' }}
        >
          <SkipForward size={28} style={{ color: 'var(--t-text-dim)', opacity: 0.5 }} />
        </motion.div>
        <p className="text-sm font-semibold mb-1.5" style={{ color: 'var(--t-text-secondary)' }}>
          Phase Skipped
        </p>
        <p className="text-xs max-w-xs leading-relaxed" style={{ color: 'var(--t-text-dim)' }}>
          This phase was skipped because a previous phase encountered errors.
        </p>
      </div>
    )
  }

  const Icon = meta?.Icon || Info

  return (
    <div className="flex flex-col gap-6">
      {/* ── Role Description Card (Big & Highlighted) ──────────── */}
      <motion.div
        {...cardPop}
        className="phase-card float-card"
        style={{ '--icon-glow-color': meta?.glowColor }}
      >
        <div className="phase-card-header">
          <div
            className="phase-card-icon"
            style={{ background: meta?.bgColor || 'rgba(124,58,237,0.12)', '--icon-glow-color': meta?.glowColor }}
          >
            <Icon size={30} style={{ color: meta?.color || '#A78BFA' }} />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-1.5">
              <span className="text-xl font-extrabold" style={{ color: 'var(--t-text)' }}>
                {meta?.roleTitle || 'Phase'}
              </span>
              <span className="text-xs font-bold px-3 py-1 rounded-lg font-mono uppercase tracking-wider"
                    style={{ background: meta?.bgColor, color: meta?.color, border: `1px solid ${meta?.borderColor}` }}>
                Phase {meta?.num}
              </span>
            </div>
            <p className="text-[0.95rem] leading-relaxed" style={{ color: 'var(--t-text-secondary)' }}>
              {meta?.roleDescription}
            </p>
          </div>
        </div>

        <div className="phase-card-body">
          {/* Detailed explanation */}
          <div className="flex items-start gap-3.5 mb-5 px-1">
            <BookOpen size={20} style={{ color: meta?.color || '#A78BFA', marginTop: 3, flexShrink: 0 }} />
            <p className="text-[0.9rem] leading-relaxed" style={{ color: 'var(--t-text-dim)' }}>
              {meta?.roleDetails}
            </p>
          </div>

          {/* What it produces */}
          <div className="flex items-start gap-4 px-4 py-4 rounded-xl"
               style={{ background: 'rgba(52, 211, 153, 0.05)', border: '1px solid rgba(52, 211, 153, 0.10)' }}>
            <Sparkles size={20} style={{ color: '#34D399', marginTop: 3, flexShrink: 0 }} />
            <div>
              <span className="text-xs font-bold tracking-wider uppercase block mb-1" style={{ color: '#34D399' }}>
                What it produces
              </span>
              <p className="text-[0.9rem] leading-relaxed" style={{ color: 'var(--t-text-secondary)' }}>
                {meta?.whatItProduces}
              </p>
            </div>
          </div>
        </div>

        {/* Status footer */}
        <div className="phase-card-footer">
          <div className="flex items-center gap-2">
            {phase.completed && !phase.errors?.length ? (
              <>
                <CheckCircle2 size={16} style={{ color: '#34D399' }} />
                <span className="text-sm font-bold" style={{ color: '#34D399' }}>Completed Successfully</span>
              </>
            ) : phase.errors?.length ? (
              <>
                <XCircle size={16} style={{ color: '#F87171' }} />
                <span className="text-sm font-bold" style={{ color: '#F87171' }}>{phase.errors.length} Error{phase.errors.length > 1 ? 's' : ''} Found</span>
              </>
            ) : (
              <span className="text-sm" style={{ color: 'var(--t-text-dim)' }}>Pending</span>
            )}
          </div>
          {phase.duration_ms !== undefined && (
            <span className="text-xs font-mono font-bold px-3 py-1 rounded-lg"
                  style={{ background: meta?.bgColor, color: meta?.color }}>
              {phase.duration_ms.toFixed(1)}ms
            </span>
          )}
        </div>
      </motion.div>

      {/* ── Errors ─────────────────────────────────────────────── */}
      {phase.errors?.length > 0 && (
        <motion.div {...fadeUp} transition={{ ...fadeUp.transition, delay: 0.1 }}>
          <div className="flex items-center gap-2 mb-3">
            <XCircle size={17} style={{ color: '#F87171' }} />
            <span className="text-sm font-bold tracking-wider uppercase"
                  style={{ color: '#F87171' }}>
              Errors Detected ({phase.errors.length})
            </span>
          </div>
          <div className="flex flex-col gap-2.5">
            {phase.errors.map((e, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className="error-item-card"
              >
                <AlertCircle size={14} className="flex-shrink-0 mt-0.5" />
                <span className="text-base">
                  {typeof e === 'string' ? e : e.message || JSON.stringify(e)}
                </span>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* ── Phase Output ───────────────────────────────────────── */}
      {phase.output && (
        <motion.div {...fadeUp} transition={{ ...fadeUp.transition, delay: 0.15 }}>
          <div className="flex items-center gap-2 mb-3">
            <CheckCircle2 size={17} style={{ color: meta?.color || '#34D399' }} />
            <span className="text-sm font-bold tracking-wider uppercase"
                  style={{ color: meta?.color || '#34D399' }}>
              Output
            </span>
          </div>
          <PhaseOutput phaseId={phase.id} output={phase.output} meta={meta} />
        </motion.div>
      )}
    </div>
  )
}


/* ═══════════════════════════════════════════════════════════════════════
   PHASE OUTPUT RENDERERS
   ═══════════════════════════════════════════════════════════════════════ */

function PhaseOutput({ phaseId, output, meta }) {
  switch (phaseId) {
    case 'lexical':
      return <TokensView tokens={output.tokens || []} />
    case 'syntax':
      return (
        <div className="flex flex-col gap-5">
          <AsciiTreeView
            title="Abstract Syntax Tree"
            ascii={output.syntax_tree_ascii || (output.syntax_tree ? JSON.stringify(output.syntax_tree, null, 2) : '')}
            icon={<GitBranch size={14} style={{ color: '#22D3EE' }} />}
            color="#22D3EE"
          />
        </div>
      )
    case 'semantic':
      return (
        <div className="flex flex-col gap-5">
          <SymbolTableView symbols={output.symbol_table || []} />
          <AsciiTreeView
            title="Type-Annotated Semantic Tree"
            ascii={output.semantic_tree_ascii || ''}
            icon={<GitBranch size={14} style={{ color: '#F472B6' }} />}
            color="#F472B6"
            highlightTypes="#F472B6"
          />
        </div>
      )
    case 'intermediate':
      return <CodeView lines={output.tac || []} label="Three-Address Code" color="#FBBF24" />
    case 'optimization':
      return <OptimizationView output={output} />
    case 'codegen':
      return <CodeView lines={output.assembly || []} label="Pseudo Assembly" color="#FB923C" />
    default:
      return <p style={{ color: 'var(--t-text-dim)' }}>No output renderer</p>
  }
}


/* ── Tokens Table ────────────────────────────────────────────────────── */
function TokensView({ tokens }) {
  if (!tokens.length) return <EmptySection text="No tokens generated" />
  return (
    <div className="rounded-2xl overflow-hidden" style={{ border: '1px solid var(--t-border-vivid)' }}>
      <table className="tokens-table-premium">
        <thead>
          <tr>
            <th>#</th>
            <th>Type</th>
            <th>Value</th>
            <th>Line</th>
          </tr>
        </thead>
        <tbody>
          {tokens.map((t, i) => (
            <motion.tr
              key={i}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: Math.min(i * 0.01, 0.4), duration: 0.15 }}
            >
              <td>{i + 1}</td>
              <td>
                <span className={`token-badge ${getTokenClass(t.type)}`}>{t.type}</span>
              </td>
              <td className="font-mono">{t.value}</td>
              <td style={{ color: 'var(--t-text-dim)' }}>{t.line}</td>
            </motion.tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}


/* ── ASCII Tree Display ──────────────────────────────────────────────── */
function HighlightedTreeLine({ text, highlightColor }) {
  // Split on type annotations like :int, :float, :void, :char, :double, :short, :long, :unsigned
  const parts = text.split(/(:[a-z_][a-z0-9_*]*)/gi)
  return parts.map((part, i) => {
    if (/^:[a-z_]/i.test(part)) {
      return (
        <span key={i} style={{
          color: highlightColor,
          textDecoration: 'underline',
          textDecorationColor: highlightColor,
          textUnderlineOffset: '3px',
          textDecorationThickness: '2px',
          fontWeight: 700,
          borderRadius: '3px',
        }}>{part}</span>
      )
    }
    return <span key={i}>{part}</span>
  })
}

function AsciiTreeView({ title, ascii, icon, color, highlightTypes }) {
  if (!ascii) return <EmptySection text="No tree generated" />
  const lines = ascii.split('\n')
  return (
    <div>
      <div className="flex items-center gap-2.5 mb-3">
        {icon}
        <span className="text-sm font-bold tracking-wider uppercase"
              style={{ color: color || '#A78BFA' }}>
          {title}
        </span>
      </div>
      <motion.div
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
        className="ascii-tree-block"
      >
        <pre className="ascii-tree-pre">{highlightTypes
          ? lines.map((line, i) => (
              <React.Fragment key={i}>
                {i > 0 && '\n'}
                <HighlightedTreeLine text={line} highlightColor={highlightTypes} />
              </React.Fragment>
            ))
          : ascii
        }</pre>
      </motion.div>
    </div>
  )
}


/* ── Symbol Table ────────────────────────────────────────────────────── */
function SymbolTableView({ symbols }) {
  if (!symbols.length) return <EmptySection text="No symbols found" />
  return (
    <div>
      <div className="flex items-center gap-2.5 mb-3">
        <Variable size={16} style={{ color: '#F472B6' }} />
        <span className="text-sm font-bold tracking-wider uppercase"
              style={{ color: '#F472B6' }}>
          Symbol Table
        </span>
      </div>
      <div className="rounded-2xl overflow-hidden" style={{ border: '1px solid var(--t-border-vivid)' }}>
        <table className="tokens-table-premium">
          <thead>
            <tr>
              <th>#</th>
              <th>Name</th>
              <th>Type</th>
              <th>Kind</th>
              <th>Scope</th>
              <th>Line</th>
            </tr>
          </thead>
          <tbody>
            {symbols.map((s, i) => (
              <motion.tr
                key={i}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.04, duration: 0.15 }}
              >
                <td>{i + 1}</td>
                <td>
                  <span className="font-mono font-bold" style={{ color: 'var(--t-text)' }}>{s.name}</span>
                </td>
                <td>
                  <span className="token-badge token-keyword">{s.type}</span>
                </td>
                <td style={{ color: 'var(--t-text-secondary)' }}>{s.kind}</td>
                <td style={{ color: 'var(--t-text-dim)' }}>{s.scope}</td>
                <td style={{ color: 'var(--t-text-dim)' }}>{s.line}</td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}


/* ── Code View (IR / Assembly) ───────────────────────────────────────── */
function CodeView({ lines, label, color }) {
  if (!lines.length) return <EmptySection text={`No ${label || 'output'}`} />
  return (
    <div>
      {label && (
        <div className="flex items-center gap-2.5 mb-3">
          <Layers size={16} style={{ color: color || '#FBBF24' }} />
          <span className="text-sm font-bold tracking-wider uppercase"
                style={{ color: color || '#FBBF24' }}>
            {label}
          </span>
        </div>
      )}
      <motion.div
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        className="rounded-2xl overflow-hidden"
        style={{ background: 'var(--t-code-bg)', border: '1px solid var(--t-border-vivid)' }}
      >
        <div className="p-4">
          {lines.map((line, i) => (
            <div className="code-line-numbered" key={i}>
              <span className="code-line-num">{i + 1}</span>
              <span className="code-line-text">{line}</span>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  )
}


/* ── Optimization View (with changes) ────────────────────────────────── */
function OptimizationView({ output }) {
  const tac = output.optimized_tac || []
  const changes = output.changes || []

  return (
    <div className="flex flex-col gap-5">
      {changes.length > 0 && (
        <div>
          <div className="flex items-center gap-2.5 mb-3">
            <Sparkles size={16} style={{ color: '#34D399' }} />
            <span className="text-sm font-bold tracking-wider uppercase"
                  style={{ color: '#34D399' }}>
              Optimizations Applied ({changes.length})
            </span>
          </div>
          <div className="flex flex-col gap-2.5">
            {changes.map((c, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.06, duration: 0.2 }}
                className="opt-change-card"
              >
                <div className="flex items-center gap-2 mb-2">
                  <Rocket size={12} style={{ color: '#34D399' }} />
                  <span className="text-xs font-bold px-3 py-1 rounded-lg uppercase tracking-wider"
                        style={{ background: 'rgba(52, 211, 153, 0.12)', color: '#34D399', border: '1px solid rgba(52, 211, 153, 0.20)' }}>
                    {c.rule}
                  </span>
                </div>
                <div className="text-base font-mono flex items-center gap-3 flex-wrap">
                  <span style={{ color: '#F87171', textDecoration: c.optimized === '(removed)' ? 'line-through' : 'line-through', opacity: 0.7 }}>{c.original}</span>
                  {c.optimized === '(removed)' ? (
                    <span className="text-xs font-bold px-2 py-0.5 rounded"
                          style={{ background: 'rgba(239,68,68,0.10)', color: '#F87171' }}>✕ removed</span>
                  ) : (
                    <>
                      <span className="text-xs font-bold px-2 py-0.5 rounded"
                            style={{ background: 'rgba(34,211,238,0.10)', color: '#22D3EE' }}>→</span>
                      <span style={{ color: '#34D399', fontWeight: 600 }}>{c.optimized}</span>
                    </>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {changes.length === 0 && (
        <motion.div {...fadeUp}
          className="flex items-center gap-3 text-[0.8rem] px-5 py-4 rounded-2xl"
          style={{ background: 'rgba(52,211,153,0.06)', color: '#34D399', border: '1px solid rgba(52,211,153,0.12)' }}
        >
          <CheckCircle2 size={16} />
          No optimizations applicable — the code has no compile-time constant expressions, redundant operations, or eliminable temporaries.
        </motion.div>
      )}

      <CodeView lines={tac} label="Optimized TAC" color="#34D399" />
    </div>
  )
}


/* ── Runtime View ────────────────────────────────────────────────────── */
function RuntimeView({ runtime }) {
  const stdout = runtime?.stdout || ''
  const stderr = runtime?.stderr || ''
  const exitCode = runtime?.exit_code ?? runtime?.returncode ?? null
  const elapsed = runtime?.execution_time_ms ?? null

  return (
    <div className="flex flex-col gap-5">
      <motion.div {...cardPop}>
        <div className="flex items-center gap-2.5 mb-3">
          <Terminal size={17} style={{ color: '#34D399' }} />
          <span className="text-sm font-bold tracking-wider uppercase"
                style={{ color: '#34D399' }}>Standard Output</span>
        </div>
        <div className={`runtime-stdout ${!stdout ? 'italic' : ''}`}
             style={!stdout ? { color: 'var(--t-text-dim)' } : undefined}>
          {stdout || '(no output)'}
        </div>
      </motion.div>

      {stderr && (
        <motion.div {...cardPop} transition={{ ...cardPop.transition, delay: 0.1 }}>
          <div className="flex items-center gap-2.5 mb-3">
            <TriangleAlert size={17} style={{ color: '#F87171' }} />
            <span className="text-sm font-bold tracking-wider uppercase"
                  style={{ color: '#F87171' }}>Standard Error</span>
          </div>
          <div className="runtime-stderr">{stderr}</div>
        </motion.div>
      )}

      <motion.div {...cardPop} transition={{ ...cardPop.transition, delay: 0.15 }}
                  className="flex items-center gap-3 pt-2">
        {exitCode !== null && (
          <span className={`inline-flex items-center gap-2 text-sm font-bold px-4 py-2 rounded-xl font-mono ${
            exitCode === 0
              ? 'text-[#34D399]'
              : 'text-[#F87171]'
          }`}
          style={{
            background: exitCode === 0 ? 'rgba(52,211,153,0.10)' : 'rgba(248,113,113,0.10)',
            border: `1px solid ${exitCode === 0 ? 'rgba(52,211,153,0.20)' : 'rgba(248,113,113,0.20)'}`,
          }}>
            {exitCode === 0 ? <Check size={12} /> : <AlertCircle size={12} />}
            Exit Code: {exitCode}
          </span>
        )}
        {elapsed !== null && (
          <span className="inline-flex items-center gap-1.5 text-sm font-bold px-4 py-2 rounded-xl font-mono"
                style={{ background: 'rgba(124,58,237,0.10)', color: '#A78BFA', border: '1px solid rgba(124,58,237,0.20)' }}>
            <Zap size={12} />
            {elapsed} ms
          </span>
        )}
      </motion.div>
    </div>
  )
}


/* ── Empty States ────────────────────────────────────────────────────── */

function EmptyState() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.92 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, type: 'spring' }}
      className="flex flex-col items-center justify-center py-20 text-center"
    >
      <motion.div
        animate={{ y: [0, -6, 0] }}
        transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
        className="w-20 h-20 rounded-3xl flex items-center justify-center mb-6"
        style={{
          background: 'linear-gradient(135deg, rgba(124,58,237,0.12), rgba(34,211,238,0.08))',
          border: '1px solid rgba(124,58,237,0.20)',
          boxShadow: '0 8px 32px rgba(124,58,237,0.10)',
        }}
      >
        <Terminal size={32} style={{ color: '#A78BFA', opacity: 0.6 }} />
      </motion.div>
      <p className="text-lg font-semibold mb-2" style={{ color: 'var(--t-text-secondary)' }}>
        Ready to Compile
      </p>
      <p className="text-base max-w-sm leading-relaxed mb-4" style={{ color: 'var(--t-text-dim)' }}>
        Write your C code in the editor and hit <strong className="gradient-text" style={{ fontWeight: 700 }}>Run Code</strong> to see all 6 compiler phases visualized in real-time.
      </p>
      <span className="text-sm font-mono font-bold px-4 py-2 rounded-xl"
        style={{ color: '#A78BFA', background: 'rgba(124,58,237,0.10)', border: '1px solid rgba(124,58,237,0.20)' }}>
        Ctrl + Enter
      </span>
    </motion.div>
  )
}

function EmptySection({ text }) {
  return (
    <div className="flex flex-col items-center justify-center py-14 text-center">
      <p className="text-sm font-medium" style={{ color: 'var(--t-text-dim)' }}>{text}</p>
    </div>
  )
}
