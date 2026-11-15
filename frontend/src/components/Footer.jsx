import { useNavigate, useLocation } from 'react-router-dom'
import { Rocket, Moon, ExternalLink } from 'lucide-react'
import './Footer.css'

const CURRENT_YEAR = new Date().getFullYear()

export default function Footer() {
  const navigate = useNavigate()
  const location = useLocation()

  const goToSection = (id) => {
    if (location.pathname !== '/') {
      navigate('/', { state: { scrollTo: id } })
      return
    }
    const el = document.getElementById(id)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <footer className="footer">
      <div className="footer-main">
        {/* Brand Column */}
        <div className="footer-brand-col">
          <div className="footer-logo">
            <div className="footer-logo-icon">
              <Moon size={16} strokeWidth={2.4} />
            </div>
            <span className="footer-brand-name">
              LUNAR <span>GUARDIANS</span>
            </span>
          </div>

          <p className="footer-brand-tagline">
            Preparing the next generation of space explorers.
          </p>

          <div className="footer-brand-badge">
            <Rocket size={13} />
            <span>NASA Space Apps Challenge</span>
          </div>
        </div>

        {/* Section 1: About Project */}
        <div>
          <h4 className="footer-col-title">About Project</h4>
          <div className="footer-links">
            <button type="button" className="footer-link" onClick={() => goToSection('hero')}>
              Mission Overview
            </button>
            <button type="button" className="footer-link" onClick={() => goToSection('features')}>
              Outpost Systems
            </button>
            <button type="button" className="footer-link" onClick={() => navigate('/mission-setup')}>
              Start Mission
            </button>
          </div>
        </div>

        {/* Section 2: How to Play */}
        <div>
          <h4 className="footer-col-title">How to Play</h4>
          <div className="footer-links">
            <button type="button" className="footer-link" onClick={() => goToSection('how-to-play')}>
              01. Establish Outpost
            </button>
            <button type="button" className="footer-link" onClick={() => goToSection('how-to-play')}>
              02. Manage Resources
            </button>
            <button type="button" className="footer-link" onClick={() => goToSection('how-to-play')}>
              03. Survive the Mission
            </button>
          </div>
        </div>

        {/* Section 3: NASA Resources */}
        <div>
          <h4 className="footer-col-title">NASA Resources</h4>
          <div className="footer-links">
            <a
              className="footer-link footer-ext-link"
              href="https://kauai.ccmc.gsfc.nasa.gov/DONKI/"
              target="_blank"
              rel="noopener noreferrer"
            >
              NASA DONKI <ExternalLink size={12} />
            </a>
            <a
              className="footer-link footer-ext-link"
              href="https://osdr.nasa.gov/"
              target="_blank"
              rel="noopener noreferrer"
            >
              NASA OSDR <ExternalLink size={12} />
            </a>
            <a
              className="footer-link footer-ext-link"
              href="https://api.nasa.gov/"
              target="_blank"
              rel="noopener noreferrer"
            >
              NASA Open APIs <ExternalLink size={12} />
            </a>
          </div>
        </div>

        {/* Section 4: Team Members */}
        <div>
          <h4 className="footer-col-title">Team Members</h4>
          <div className="footer-links">
            <span className="footer-team-item">Lunar Guardians Crew</span>
            <span className="footer-team-role">Mission Architecture &amp; UI</span>
            <span className="footer-team-role">Space Science &amp; Education</span>
            <span className="footer-team-role">Full-Stack Simulation Dev</span>
          </div>
        </div>
      </div>

      <div className="footer-bottom">
        <p>&copy; {CURRENT_YEAR} LUNAR GUARDIANS — Junior Astronaut Mission Trainer.</p>
        <p className="footer-attribution-note">
          Data Attribution: Educational concepts informed by publicly available{' '}
          <a href="https://api.nasa.gov/" target="_blank" rel="noopener noreferrer">
            NASA Open Science &amp; DONKI/OSDR datasets
          </a>
          . Independent student project; not officially endorsed by NASA.
        </p>
      </div>
    </footer>
  )
}
