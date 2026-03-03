import React, { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronRight, ChevronDown, GitBranch } from 'lucide-react'

/* ── Node-type colour categories ──────────────────────────────────────── */
const CAT = {
  program:  'ast-cat-program',
  func:     'ast-cat-func',
  stmt:     'ast-cat-stmt',
  decl:     'ast-cat-decl',
  expr:     'ast-cat-expr',
  literal:  'ast-cat-literal',
  default:  'ast-cat-default',
}

const TYPE_MAP = {
  Program: CAT.program, TranslationUnit: CAT.program,
  FunctionDef: CAT.func, FunctionDecl: CAT.func, FunctionCall: CAT.func,
  ParamList: CAT.func, Param: CAT.func,
  CompoundStmt: CAT.stmt, ReturnStmt: CAT.stmt, IfStmt: CAT.stmt,
  WhileStmt: CAT.stmt, ForStmt: CAT.stmt, DoWhileStmt: CAT.stmt,
  SwitchStmt: CAT.stmt, CaseStmt: CAT.stmt, DefaultStmt: CAT.stmt,
  ExprStmt: CAT.stmt, BreakStmt: CAT.stmt, ContinueStmt: CAT.stmt,
  VarDecl: CAT.decl, ArrayDecl: CAT.decl, StructDecl: CAT.decl,
  BinaryExpr: CAT.expr, UnaryExpr: CAT.expr, AssignExpr: CAT.expr,
  TernaryExpr: CAT.expr, CastExpr: CAT.expr, PostfixExpr: CAT.expr,
  Identifier: CAT.literal, IntLiteral: CAT.literal, FloatLiteral: CAT.literal,
  StringLiteral: CAT.literal, CharLiteral: CAT.literal,
}

function catOf(type) {
  if (TYPE_MAP[type]) return TYPE_MAP[type]
  const t = (type || '').toLowerCase()
  if (t.includes('func') || t.includes('call')) return CAT.func
  if (t.includes('stmt') || t.includes('statement')) return CAT.stmt
  if (t.includes('decl')) return CAT.decl
  if (t.includes('expr')) return CAT.expr
  if (t.includes('literal') || t.includes('ident')) return CAT.literal
  return CAT.default
}

/* ── Single tree node ─────────────────────────────────────────────────── */
function ASTNode({ node, depth = 0, idx = 0, defaultOpen }) {
  const [expanded, setExpanded] = useState(defaultOpen ? true : depth < 3)
  const hasKids = node.children && node.children.length > 0
  const cat = catOf(node.type)

  return (
    <div className="ast-node-wrap">
      <motion.div
        initial={{ opacity: 0, x: -6 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: Math.min(idx * 0.015, 0.25), duration: 0.15 }}
        className="ast-row"
        style={{ paddingLeft: `${depth * 20}px` }}
      >
        {/* toggle */}
        <button
          onClick={() => hasKids && setExpanded(v => !v)}
          className={`ast-toggle ${hasKids ? '' : 'invisible'}`}
          aria-label={expanded ? 'Collapse' : 'Expand'}
          tabIndex={hasKids ? 0 : -1}
        >
          {hasKids && (expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />)}
        </button>

        {/* connector dot */}
        {depth > 0 && <span className="ast-dot" />}

        {/* type badge */}
        <span className={`ast-badge ${cat}`}>{node.type}</span>

        {/* value */}
        {node.value && <span className="ast-val">{node.value}</span>}

        {/* child count */}
        {hasKids && <span className="ast-count">{node.children.length}</span>}
      </motion.div>

      <AnimatePresence>
        {expanded && hasKids && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.18 }}
            className="overflow-hidden"
          >
            <div className="ast-children" style={{ marginLeft: `${depth * 20 + 10}px` }}>
              {node.children.map((c, i) => (
                <ASTNode key={i} node={c} depth={depth + 1} idx={i} defaultOpen={defaultOpen} />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

/* ── Count all nodes for stats badge ──────────────────────────────────── */
function countNodes(n) {
  if (!n) return 0
  let c = 1
  if (n.children) n.children.forEach(ch => { c += countNodes(ch) })
  return c
}

/* ── Exported component ───────────────────────────────────────────────── */
export default function SyntaxTree({ ast }) {
  const [expandKey, setExpandKey] = useState(0)
  const [allOpen, setAllOpen] = useState(false)
  const total = useMemo(() => countNodes(ast), [ast])

  if (!ast) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="w-16 h-16 rounded-2xl ast-empty-icon flex items-center justify-center mb-5">
          <GitBranch size={28} />
        </div>
        <p className="text-sm ast-empty-text max-w-xs leading-relaxed">
          Compile your code to see the <strong>Abstract Syntax Tree</strong> visualized here.
        </p>
      </div>
    )
  }

  const toggleAll = () => {
    setAllOpen(v => !v)
    setExpandKey(k => k + 1)
  }

  return (
    <div className="flex flex-col h-full">
      {/* toolbar */}
      <div className="ast-toolbar">
        <div className="flex items-center gap-2">
          <GitBranch size={13} style={{ color: '#6366F1' }} />
          <span className="ast-toolbar-label">Abstract Syntax Tree</span>
          <span className="ast-toolbar-stat">{total} nodes</span>
        </div>
        <button onClick={toggleAll} className="ast-toolbar-btn">
          {allOpen ? 'Collapse All' : 'Expand All'}
        </button>
      </div>

      {/* tree */}
      <div className="flex-1 min-h-0 overflow-auto custom-scrollbar p-4">
        <ASTNode key={expandKey} node={ast} defaultOpen={allOpen} />
      </div>
    </div>
  )
}
