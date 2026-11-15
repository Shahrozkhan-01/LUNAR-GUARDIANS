import { motion } from 'framer-motion'
import { Building2, Sliders, ShieldCheck } from 'lucide-react'
import './HowToPlay.css'

const STEPS = [
  {
    number: '01',
    stepBadge: 'STEP 01 — ESTABLISH YOUR OUTPOST',
    title: 'Establish Your Outpost',
    desc: 'Prepare your lunar habitat and mission systems.',
    detail: 'Deploy your pressurized crew dome, initialize solar arrays, and bring life-support modules online across the lunar surface.',
    icon: Building2,
    accent: '#00e5ff',
    visual: 'outpost',
  },
  {
    number: '02',
    stepBadge: 'STEP 02 — MANAGE YOUR RESOURCES',
    title: 'Manage Your Resources',
    desc: 'Balance power, oxygen, water, food, and radiation protection.',
    detail: 'Monitor outpost reserves carefully and route electricity between life support, hydroponics, and habitat defense.',
    icon: Sliders,
    accent: '#8b5cf6',
    visual: 'resources',
  },
  {
    number: '03',
    stepBadge: 'STEP 03 — SURVIVE THE MISSION',
    title: 'Survive the Mission',
    desc: 'Make difficult decisions and overcome unexpected space events.',
    detail: 'Adapt quickly when solar storms strike, protect your junior astronaut crew, and guide your outpost safely through every mission day.',
    icon: ShieldCheck,
    accent: '#ff6b35',
    visual: 'survive',
  },
]

function StepIllustration({ type }) {
  if (type === 'outpost') {
    return (
      <svg className="step-svg" viewBox="0 0 260 96" fill="none" aria-hidden="true">
        <path d="M10 82 Q75 68 130 76 T250 78" stroke="rgba(0,229,255,0.3)" strokeWidth="1.5" />
        <path d="M88 76 A42 34 0 0 1 172 76 Z" fill="rgba(0,229,255,0.08)" stroke="#00e5ff" strokeWidth="1.5" />
        <path d="M108 76 A22 18 0 0 1 152 76" stroke="rgba(0,229,255,0.45)" strokeWidth="1.2" />
        <line x1="130" y1="42" x2="130" y2="24" stroke="#00e5ff" strokeWidth="1.5" />
        <circle cx="130" cy="21" r="3.5" fill="#00e5ff" />
        <rect x="44" y="54" width="28" height="10" rx="2" transform="rotate(-14 44 54)" fill="rgba(59,130,246,0.22)" stroke="#38bdf8" strokeWidth="1.2" />
        <line x1="58" y1="62" x2="58" y2="75" stroke="#38bdf8" strokeWidth="1.4" />
        <rect x="188" y="50" width="28" height="10" rx="2" transform="rotate(14 188 50)" fill="rgba(59,130,246,0.22)" stroke="#38bdf8" strokeWidth="1.2" />
        <line x1="200" y1="62" x2="200" y2="76" stroke="#38bdf8" strokeWidth="1.4" />
      </svg>
    )
  }

  if (type === 'resources') {
    return (
      <svg className="step-svg" viewBox="0 0 260 96" fill="none" aria-hidden="true">
        <rect x="28" y="22" width="204" height="52" rx="10" fill="rgba(139,92,246,0.07)" stroke="rgba(139,92,246,0.35)" strokeWidth="1.2" />
        <rect x="46" y="34" width="110" height="6" rx="3" fill="#00e5ff" opacity="0.85" />
        <rect x="46" y="34" width="168" height="6" rx="3" fill="rgba(255,255,255,0.08)" />
        <rect x="46" y="46" width="138" height="6" rx="3" fill="#a855f7" opacity="0.85" />
        <rect x="46" y="46" width="168" height="6" rx="3" fill="rgba(255,255,255,0.08)" />
        <rect x="46" y="58" width="92" height="6" rx="3" fill="#22c55e" opacity="0.85" />
        <rect x="46" y="58" width="168" height="6" rx="3" fill="rgba(255,255,255,0.08)" />
      </svg>
    )
  }

  return (
    <svg className="step-svg" viewBox="0 0 260 96" fill="none" aria-hidden="true">
      <circle cx="58" cy="48" r="18" fill="rgba(255,107,53,0.2)" stroke="#ff6b35" strokeWidth="1.5" />
      <path d="M86 30 Q106 48 86 66" stroke="rgba(255,107,53,0.65)" strokeWidth="1.5" strokeDasharray="4 4" />
      <path d="M104 22 Q130 48 104 74" stroke="rgba(255,107,53,0.45)" strokeWidth="1.5" strokeDasharray="4 4" />
      <path d="M156 22 A34 34 0 0 0 156 74" stroke="#00e5ff" strokeWidth="2.2" />
      <path d="M188 38 L198 48 L218 28" stroke="#22c55e" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

const cardVariants = {
  hidden: { opacity: 0, y: 36 },
  visible: (i) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.16, duration: 0.6, ease: 'easeOut' },
  }),
}

export default function HowToPlay() {
  return (
    <section className="howtoplay-section" id="how-to-play">
      <motion.div
        className="section-header"
        initial={{ opacity: 0, y: 24 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-80px' }}
        transition={{ duration: 0.6 }}
      >
        <span className="section-label">Mission Protocol</span>
        <h2 className="section-title">YOUR JOURNEY STARTS HERE</h2>
        <p className="section-subtitle">
          Follow three core command phases to build, balance, and protect humanity&apos;s lunar outpost.
        </p>
      </motion.div>

      <div className="howtoplay-wrapper">
        <div className="howtoplay-connector-line" aria-hidden="true" />

        <div className="howtoplay-steps">
          {STEPS.map((step, i) => {
            const Icon = step.icon
            return (
              <motion.article
                key={step.number}
                className="step-card"
                style={{ '--step-accent': step.accent }}
                custom={i}
                variants={cardVariants}
                initial="hidden"
                whileInView="visible"
                whileHover={{ y: -6 }}
                viewport={{ once: true, margin: '-60px' }}
              >
                <div className="step-card-header">
                  <div className="step-number-badge">
                    <Icon size={20} />
                    <span>{step.number}</span>
                  </div>
                  <span className="step-tag">{step.stepBadge}</span>
                </div>

                <div className="step-visual-box">
                  <StepIllustration type={step.visual} />
                </div>

                <h3 className="step-title">{step.title}</h3>
                <p className="step-lead">{step.desc}</p>
                <p className="step-detail">{step.detail}</p>
              </motion.article>
            )
          })}
        </div>
      </div>
    </section>
  )
}
