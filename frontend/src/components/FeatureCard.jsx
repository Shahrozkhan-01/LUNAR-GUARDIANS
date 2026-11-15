import { motion } from 'framer-motion'
import { Wind, Zap, ShieldAlert, Sprout } from 'lucide-react'
import './FeatureCard.css'

const MISSION_FEATURES = [
  {
    code: 'SYS-01 // LIFE SUPPORT',
    icon: Wind,
    title: 'Life Support',
    description: 'Manage oxygen and water to keep your astronauts alive.',
    accentColor: '#00e5ff',
    glowColor: 'rgba(0, 229, 255, 0.22)',
    iconBg: 'rgba(0, 229, 255, 0.12)',
  },
  {
    code: 'SYS-02 // ENERGY GRID',
    icon: Zap,
    title: 'Power Management',
    description: 'Distribute limited electricity between critical outpost systems.',
    accentColor: '#38bdf8',
    glowColor: 'rgba(56, 189, 248, 0.22)',
    iconBg: 'rgba(56, 189, 248, 0.12)',
  },
  {
    code: 'SYS-03 // SHIELD ARRAY',
    icon: ShieldAlert,
    title: 'Radiation Protection',
    description: 'Respond to solar storms and protect your crew.',
    accentColor: '#ff6b35',
    glowColor: 'rgba(255, 107, 53, 0.24)',
    iconBg: 'rgba(255, 107, 53, 0.12)',
  },
  {
    code: 'SYS-04 // HYDROPONICS',
    icon: Sprout,
    title: 'Food Production',
    description: 'Grow food while balancing electricity and water consumption.',
    accentColor: '#a855f7',
    glowColor: 'rgba(168, 85, 247, 0.24)',
    iconBg: 'rgba(168, 85, 247, 0.12)',
  },
]

const cardVariants = {
  hidden: { opacity: 0, y: 36 },
  visible: (index) => ({
    opacity: 1,
    y: 0,
    transition: { delay: index * 0.12, duration: 0.55, ease: 'easeOut' },
  }),
}

export default function FeatureCard({
  icon: Icon,
  code,
  title,
  description,
  accentColor = '#00e5ff',
  glowColor = 'rgba(0, 229, 255, 0.22)',
  iconBg = 'rgba(0, 229, 255, 0.12)',
  index = 0,
}) {
  return (
    <motion.article
      className="feature-card"
      style={{
        '--card-accent': accentColor,
        '--card-glow': glowColor,
        '--icon-bg': iconBg,
      }}
      custom={index}
      variants={cardVariants}
      initial="hidden"
      whileInView="visible"
      whileHover={{ y: -8 }}
      viewport={{ once: true, margin: '-60px' }}
    >
      <div className="feature-card-top">
        <div className="feature-icon-wrap">
          <Icon size={26} strokeWidth={2} />
        </div>
        {code && <span className="feature-sys-code">{code}</span>}
      </div>

      <h3 className="feature-title">{title}</h3>
      <p className="feature-desc">{description}</p>

      <div className="feature-card-corner" aria-hidden="true" />
    </motion.article>
  )
}

export function MissionFeaturesSection() {
  return (
    <section className="features-section" id="features">
      <div className="features-ambient-glow" aria-hidden="true" />

      <motion.div
        className="section-header"
        initial={{ opacity: 0, y: 24 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-80px' }}
        transition={{ duration: 0.6 }}
      >
        <span className="section-label">Outpost Systems</span>
        <h2 className="section-title">EVERY DECISION COUNTS</h2>
        <p className="section-subtitle">
          Survival on the Moon requires more than courage. It requires smart engineering decisions.
        </p>
      </motion.div>

      <div className="features-grid">
        {MISSION_FEATURES.map((feature, index) => (
          <FeatureCard
            key={feature.title}
            index={index}
            code={feature.code}
            icon={feature.icon}
            title={feature.title}
            description={feature.description}
            accentColor={feature.accentColor}
            glowColor={feature.glowColor}
            iconBg={feature.iconBg}
          />
        ))}
      </div>
    </section>
  )
}
