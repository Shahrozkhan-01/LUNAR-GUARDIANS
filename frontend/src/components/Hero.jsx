import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Rocket, Compass } from 'lucide-react'
import './Hero.css'

export default function Hero() {
  const navigate = useNavigate()

  const scrollToSection = (id) => {
    const el = document.getElementById(id)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <section className="hero-section" id="hero">
      <div className="hero-bg" aria-hidden="true">
        <div className="hero-bg-image" />
        <div className="hero-bg-gradient" />
        <div className="hero-hud-grid" />
      </div>

      <motion.div
        className="hero-content"
        initial={{ opacity: 0, y: 28 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.85, ease: 'easeOut' }}
      >
        <motion.div
          className="mission-status"
          initial={{ opacity: 0, scale: 0.92 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.25, duration: 0.5 }}
        >
          <span className="status-dot" aria-hidden="true" />
          <span>MISSION STATUS: AWAITING COMMANDER</span>
        </motion.div>

        <motion.h1
          className="hero-heading"
          initial={{ opacity: 0, y: 22 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.7 }}
        >
          <span className="line">YOUR MISSION.</span>
          <span className="line accent">YOUR CREW.</span>
          <span className="line">YOUR SURVIVAL.</span>
        </motion.h1>

        <motion.p
          className="hero-subtitle"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.58, duration: 0.7 }}
        >
          Become the commander of humanity&apos;s next lunar outpost. Manage resources,
          protect your astronauts, and make decisions that determine the future of your mission.
        </motion.p>

        <motion.div
          className="hero-buttons"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.75, duration: 0.7 }}
        >
          <button
            type="button"
            className="btn-primary"
            onClick={() => navigate('/mission-setup')}
          >
            <Rocket size={18} />
            START YOUR MISSION
          </button>

          <button
            type="button"
            className="btn-secondary"
            onClick={() => scrollToSection('how-to-play')}
          >
            <Compass size={18} />
            EXPLORE THE MISSION
          </button>
        </motion.div>
      </motion.div>

      <button
        type="button"
        className="scroll-indicator"
        onClick={() => scrollToSection('features')}
        aria-label="Scroll down to Mission Features"
      >
        <span className="scroll-mouse">
          <span className="scroll-wheel" />
        </span>
        <span>SCROLL TO BRIEFING</span>
      </button>
    </section>
  )
}
