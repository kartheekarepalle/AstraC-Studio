import React from 'react'
import { motion } from 'framer-motion'
import { AlertTriangle, X } from 'lucide-react'

export default function HealthBanner({ health, dismissed, onDismiss }) {
  if (!health || health.ok || dismissed) return null

  return (
    <motion.div
      initial={{ height: 0, opacity: 0 }}
      animate={{ height: 'auto', opacity: 1 }}
      exit={{ height: 0, opacity: 0 }}
      transition={{ duration: 0.3, ease: [0.25, 0.46, 0.45, 0.94] }}
      className="relative z-20 health-banner-premium"
    >
      <div className="flex items-center justify-between px-6 py-2.5">
        <div className="flex items-center gap-2.5">
          <AlertTriangle size={15} style={{ color: '#F59E0B' }} />
          <span className="text-xs" style={{ color: 'var(--t-text-secondary)' }}>
            <strong style={{ color: '#F59E0B', fontWeight: 600 }}>GCC not found</strong>
            {' — '}Install MinGW-w64 or set the GCC path so the compiler can generate assembly and run your code.
          </span>
        </div>
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={onDismiss}
          className="p-1 rounded-md transition-colors cursor-pointer"
          style={{ color: 'var(--t-text-dim)' }}
          aria-label="Dismiss"
        >
          <X size={14} />
        </motion.button>
      </div>
    </motion.div>
  )
}
