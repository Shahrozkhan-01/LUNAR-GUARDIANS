import { motion } from 'framer-motion'
import './CrewCard.css'

function AstronautAvatar({ visorColor }) {
  return (
    <svg className="crew-avatar-svg" viewBox="0 0 64 64" fill="none" aria-hidden="true">
      <rect x="14" y="28" width="36" height="26" rx="6" fill="#1e293b" stroke="rgba(255,255,255,0.2)" strokeWidth="1.5" />
      <path d="M12 58 C12 44 20 39 32 39 C44 39 52 44 52 58" fill="#e2e8f0" stroke="#94a3b8" strokeWidth="1.5" />
      <rect x="25" y="46" width="14" height="9" rx="2" fill="#0f172a" stroke={visorColor} strokeWidth="1.2" />
      <circle cx="32" cy="25" r="16" fill="#f8fafc" stroke="#cbd5e1" strokeWidth="1.8" />
      <rect x="20" y="17" width="24" height="15" rx="7.5" fill="#090d1f" stroke={visorColor} strokeWidth="1.6" />
      <path d="M24 21 Q32 18 40 21" stroke={visorColor} strokeWidth="1.6" strokeLinecap="round" opacity="0.85" />
    </svg>
  )
}

export default function CrewCard({
  numberLabel,
  role,
  condition = 'Healthy',
  visorColor = '#00e5ff',
  index = 0,
}) {
  const toneClass =
    condition === 'Critical'
      ? 'critical'
      : condition === 'Warning'
      ? 'warning'
      : 'healthy'

  return (
    <motion.article
      className="crew-card"
      style={{ '--crew-accent': visorColor }}
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.35 }}
      whileHover={{ y: -3 }}
    >
      <div className="crew-avatar-wrap">
        <AstronautAvatar visorColor={visorColor} />
      </div>

      <div className="crew-info">
        <span className="crew-number">{numberLabel}</span>
        <h4 className="crew-role">{role}</h4>
        <div className={`crew-condition ${toneClass}`}>
          <span className="crew-condition-dot" aria-hidden="true" />
          <span>Condition: {condition} (Simulated)</span>
        </div>
      </div>
    </motion.article>
  )
}
