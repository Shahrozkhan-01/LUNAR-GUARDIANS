import { motion } from 'framer-motion'
import { ChevronRight } from 'lucide-react'
import './SystemCard.css'

export default function SystemCard({
  icon: Icon,
  name,
  code,
  statusText = 'Operational',
  accentColor = '#00e5ff',
  onClick,
  index = 0,
}) {
  return (
    <motion.button
      type="button"
      className="system-card-btn"
      style={{ '--sys-accent': accentColor }}
      onClick={onClick}
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06, duration: 0.38 }}
      whileHover={{ y: -3 }}
      whileTap={{ scale: 0.985 }}
    >
      <div className="system-card-icon">
        <Icon size={22} strokeWidth={2.1} />
      </div>

      <div className="system-card-body">
        <span className="system-card-code">{code}</span>
        <span className="system-card-name">{name}</span>
        <span className="system-card-status">
          <span className="system-card-dot" aria-hidden="true" />
          {statusText}
        </span>
      </div>

      <div className="system-card-arrow" aria-hidden="true">
        <span>Inspect</span>
        <ChevronRight size={16} />
      </div>
    </motion.button>
  )
}
