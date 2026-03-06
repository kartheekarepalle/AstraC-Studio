import React from 'react'
import { motion } from 'framer-motion'

export default function Spinner() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.25 }}
      className="fixed inset-0 z-50 flex flex-col items-center justify-center"
      style={{ background: 'var(--t-overlay)', backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)' }}
    >
      <motion.div
        initial={{ scale: 0.85, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.1, duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
        className="flex flex-col items-center gap-6 p-12 rounded-3xl"
        style={{
          background: 'var(--t-card)',
          backdropFilter: 'blur(28px)',
          border: '1px solid var(--t-border-vivid)',
          boxShadow: 'var(--t-shadow-lg), var(--t-shadow-glow)'
        }}
      >
        {/* Crystal double-orbit spinner */}
        <div className="relative flex items-center justify-center" style={{ width: 70, height: 70 }}>
          <div className="spinner-pulse-bg" />
          <div className="spinner-orbit-ring" />
          <div className="spinner-orbit-ring-2" />
          {/* Center dot */}
          <motion.div
            animate={{ scale: [1, 1.3, 1], opacity: [0.6, 1, 0.6] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
            className="absolute w-3 h-3 rounded-full"
            style={{ background: 'linear-gradient(135deg, #A78BFA, #22D3EE)' }}
          />
        </div>
        <div className="flex flex-col items-center gap-2">
          <span className="text-sm font-bold gradient-text">Compiling & Running</span>
          <span className="text-[0.65rem] font-mono" style={{ color: 'var(--t-text-dim)' }}>
            Processing your code through all 6 phases…
          </span>
        </div>
      </motion.div>
    </motion.div>
  )
}
