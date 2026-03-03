import React from 'react'
import { motion } from 'framer-motion'

export default function Spinner() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.2 }}
      className="fixed inset-0 z-50 flex flex-col items-center justify-center"
      style={{ background: 'var(--t-overlay)', backdropFilter: 'blur(8px)', WebkitBackdropFilter: 'blur(8px)' }}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.1, duration: 0.3, ease: [0.25, 0.46, 0.45, 0.94] }}
        className="flex flex-col items-center gap-5 p-10 rounded-2xl"
        style={{
          background: 'var(--t-card)',
          backdropFilter: 'blur(24px)',
          border: '1px solid var(--t-glass-border)',
          boxShadow: 'var(--t-shadow-lg)'
        }}
      >
        <div className="premium-spinner" />
        <div className="flex flex-col items-center gap-1.5">
          <span className="text-sm font-semibold" style={{ color: 'var(--t-text)' }}>Compiling & Running</span>
          <span className="text-[0.65rem] font-mono" style={{ color: 'var(--t-text-dim)' }}>AstraC Studio — Processing your code…</span>
        </div>
      </motion.div>
    </motion.div>
  )
}
