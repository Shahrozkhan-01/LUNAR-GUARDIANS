import { motion } from 'framer-motion'
import { Satellite, Database, ExternalLink, Info } from 'lucide-react'
import './NasaScience.css'

const NASA_RESOURCES = [
  {
    icon: Satellite,
    badge: 'Space Weather Archive',
    title: 'NASA DONKI',
    fullName: 'Space Weather Database of Notifications, Knowledge, Information',
    desc: 'NASA DONKI records real solar activity, including solar flares and solar energetic particle events. We show those observations separately from the game: a timed particle event can introduce a shelter decision, but DONKI does not tell us the radiation dose at a lunar outpost.',
    link: 'https://kauai.ccmc.gsfc.nasa.gov/DONKI/',
    linkText: 'Explore NASA DONKI',
    accent: '#00e5ff',
  },
  {
    icon: Database,
    badge: 'Space Biology & Health',
    title: 'NASA OSDR',
    fullName: 'Open Science Data Repository',
    desc: "NASA's Open Science Data Repository provides open access to spaceflight biological studies and astronaut health research. Insights from space biology and habitat experiments help us craft age-appropriate educational content on plant growth, radiation shielding, and human survival beyond Earth.",
    link: 'https://osdr.nasa.gov/',
    linkText: 'Explore NASA OSDR',
    accent: '#8b5cf6',
  },
]

export default function NasaScience() {
  return (
    <section className="nasa-section" id="nasa-science">
      <div className="nasa-ambient-glow" aria-hidden="true" />

      <motion.div
        className="section-header"
        initial={{ opacity: 0, y: 24 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-80px' }}
        transition={{ duration: 0.6 }}
      >
        <span className="section-label">Open Science Integration</span>
        <h2 className="section-title">POWERED BY REAL SPACE SCIENCE</h2>
        <p className="section-subtitle">
          LUNAR GUARDIANS uses authentic NASA open science resources to turn space exploration
          concepts into an engaging educational adventure for young learners.
        </p>
      </motion.div>

      <div className="nasa-cards">
        {NASA_RESOURCES.map((item, i) => {
          const Icon = item.icon
          return (
            <motion.article
              key={item.title}
              className="nasa-card"
              style={{ '--nasa-accent': item.accent }}
              initial={{ opacity: 0, y: 32 }}
              whileInView={{ opacity: 1, y: 0 }}
              whileHover={{ y: -6 }}
              viewport={{ once: true, margin: '-60px' }}
              transition={{ delay: i * 0.16, duration: 0.6 }}
            >
              <div className="nasa-card-header">
                <div className="nasa-icon-box">
                  <Icon size={24} />
                </div>
                <span className="nasa-card-badge">{item.badge}</span>
              </div>

              <h3 className="nasa-card-title">{item.title}</h3>
              <p className="nasa-card-full-name">{item.fullName}</p>
              <p className="nasa-card-desc">{item.desc}</p>

              <a
                className="nasa-card-link"
                href={item.link}
                target="_blank"
                rel="noopener noreferrer"
              >
                <span>{item.linkText}</span>
                <ExternalLink size={15} />
              </a>
            </motion.article>
          )
        })}
      </div>

      <motion.div
        className="nasa-attribution"
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ delay: 0.25, duration: 0.6 }}
      >
        <div className="nasa-attribution-icon" aria-hidden="true">
          <Info size={18} />
        </div>
        <p>
          <strong>NASA Open Data Attribution:</strong> Space science references are sourced from publicly
          available NASA resources, including{' '}
          <a href="https://kauai.ccmc.gsfc.nasa.gov/DONKI/" target="_blank" rel="noopener noreferrer">
            NASA CCMC DONKI
          </a>
          ,{' '}
          <a href="https://osdr.nasa.gov/" target="_blank" rel="noopener noreferrer">
            NASA OSDR
          </a>
          , and{' '}
          <a href="https://api.nasa.gov/" target="_blank" rel="noopener noreferrer">
            NASA Open APIs
          </a>
          . LUNAR GUARDIANS is an independent student project developed for the NASA Space Apps Challenge
          and is not officially endorsed by, sponsored by, or affiliated with NASA. Gameplay mechanics
          use simplified educational models and are clearly distinguished from real scientific measurements.
        </p>
      </motion.div>
    </section>
  )
}
