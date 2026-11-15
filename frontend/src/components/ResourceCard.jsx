import { motion } from 'framer-motion'
import './ResourceCard.css'

function getStatusInfo(value) {
  if (value >= 70) {
    return { label: 'Optimal', tone: 'optimal' }
  }
  if (value >= 35) {
    return { label: 'Nominal', tone: 'nominal' }
  }
  return { label: 'Low Alert', tone: 'caution' }
}

export default function ResourceCard({
  icon: Icon,
  name,
  value,
  unit = 'UNITS',
  accentColor = '#00e5ff',
  index = 0,
}) {
  const rounded = Math.round(value * 10) / 10
  const status = getStatusInfo(rounded)

  return (
    <motion.article
      className="resource-card"
      style={{ '--res-accent': accentColor }}
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.35 }}
      whileHover={{ y: -3 }}
    >
      <div className="resource-card-top">
        <div className="resource-icon-box">
          <Icon size={20} strokeWidth={2.2} />
        </div>
        <span className={`resource-status-pill ${status.tone}`}>
          <span className="resource-status-dot" aria-hidden="true" />
          {status.label}
        </span>
      </div>

      <div className="resource-value-row">
        <h3 className="resource-name">{name}</h3>
        <span className="resource-value">
          {rounded}
          <small>{unit}</small>
        </span>
      </div>

      <div
        className="resource-bar-track"
        role="progressbar"
        aria-valuenow={rounded}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`${name} simulated game units`}
      >
        <div
          className="resource-bar-fill"
          style={{ width: `${Math.min(100, Math.max(0, rounded))}%` }}
        />
      </div>

      <span className="resource-sim-caption">SIMULATED GAME UNITS (MAX 100)</span>
    </motion.article>
  )
}
