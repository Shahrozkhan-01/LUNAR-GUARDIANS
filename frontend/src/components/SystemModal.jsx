import { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Sparkles, CheckCircle2, Info } from 'lucide-react'
import './SystemModal.css'

export default function SystemModal({ system, icon: Icon, onClose }) {
  useEffect(() => {
    if (!system) return undefined
    const onKeyDown = (e) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [system, onClose])

  return (
    <AnimatePresence>
      {system && (
        <motion.div
          className="sys-modal-backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          role="dialog"
          aria-modal="true"
          aria-labelledby="sys-modal-title"
        >
          <motion.div
            className="sys-modal-panel"
            style={{ '--modal-accent': system.accent }}
            initial={{ opacity: 0, scale: 0.93, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 12 }}
            transition={{ duration: 0.25, ease: 'easeOut' }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="sys-modal-header">
              <div className="sys-modal-title-group">
                {Icon && (
                  <div className="sys-modal-icon">
                    <Icon size={26} />
                  </div>
                )}
                <div>
                  <span className="sys-modal-code">{system.code}</span>
                  <h2 id="sys-modal-title" className="sys-modal-title">
                    {system.name}
                  </h2>
                </div>
              </div>

              <button
                type="button"
                className="sys-modal-close"
                onClick={onClose}
                aria-label="Close system modal"
              >
                <X size={20} />
              </button>
            </div>

            <div className="sys-modal-badges">
              <span className="sys-modal-status-badge">{system.status}</span>
              <span className="sys-modal-sim-badge">SIMULATED GAME DATA</span>
            </div>

            <div className="sys-modal-section">
              <h3 className="sys-modal-heading">How This Outpost System Works</h3>
              <p className="sys-modal-text">{system.overview}</p>
            </div>

            <div className="sys-modal-fact-box">
              <div className="sys-modal-fact-icon" aria-hidden="true">
                <Sparkles size={18} />
              </div>
              <div>
                <strong>Junior Astronaut Science Fact:</strong>
                <p>{system.educationalFact}</p>
              </div>
            </div>

            <div className="sys-modal-section">
              <h3 className="sys-modal-heading">Commander Controls (Upcoming Simulation Phase)</h3>
              <ul className="sys-modal-list">
                {system.upcomingControls.map((item) => (
                  <li key={item}>
                    <CheckCircle2 size={16} />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="sys-modal-footer-note">
              <Info size={15} />
              <span>
                Informative module preview — active resource calculations and NASA DONKI space
                weather integration will be unlocked in the next phase.
              </span>
            </div>

            <div className="sys-modal-actions">
              <button type="button" className="sys-modal-done-btn" onClick={onClose}>
                Acknowledge Briefing
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
