import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Menu, X, Rocket, Moon } from 'lucide-react'
import SoundEffects from './SoundEffects.jsx'
import './Navbar.css'

const NAV_ITEMS = [
  { label: 'Home', target: 'hero' },
  { label: 'About', target: 'features' },
  { label: 'How to Play', target: 'how-to-play' },
  { label: 'NASA Data', target: 'nasa-science' },
  { label: 'Data Explorer', path: '/nasa-data' },
]

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [activeSection, setActiveSection] = useState('hero')
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    const onScroll = () => {
      setScrolled(window.scrollY > 32)

      if (location.pathname === '/') {
        const scrollPosition = window.scrollY + 180
        for (let i = NAV_ITEMS.length - 1; i >= 0; i--) {
          if (!NAV_ITEMS[i].target) continue
          const section = document.getElementById(NAV_ITEMS[i].target)
          if (section && section.offsetTop <= scrollPosition) {
            setActiveSection(NAV_ITEMS[i].target)
            break
          }
        }
      }
    }

    window.addEventListener('scroll', onScroll, { passive: true })
    onScroll()
    return () => window.removeEventListener('scroll', onScroll)
  }, [location.pathname])

  // Lock body scroll & support Escape key when mobile drawer is open
  useEffect(() => {
    document.body.style.overflow = mobileOpen ? 'hidden' : ''
    const onKeyDown = (e) => {
      if (e.key === 'Escape') setMobileOpen(false)
    }
    if (mobileOpen) {
      window.addEventListener('keydown', onKeyDown)
    }
    return () => {
      document.body.style.overflow = ''
      window.removeEventListener('keydown', onKeyDown)
    }
  }, [mobileOpen])

  const scrollToSection = (id) => {
    setMobileOpen(false)
    if (location.pathname !== '/') {
      navigate('/', { state: { scrollTo: id } })
      return
    }
    const el = document.getElementById(id)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  const handleStartMission = () => {
    setMobileOpen(false)
    navigate('/mission-setup')
  }

  const handleNavItem = (item) => {
    if (item.path) {
      setMobileOpen(false)
      navigate(item.path)
      return
    }
    scrollToSection(item.target)
  }

  return (
    <>
      <header className={`navbar${scrolled ? ' scrolled' : ''}`}>
        <div className="navbar-inner">
          <button
            type="button"
            className="nav-logo"
            onClick={() => scrollToSection('hero')}
            aria-label="Lunar Guardians Home"
          >
            <div className="nav-logo-icon">
              <Moon size={18} strokeWidth={2.4} />
            </div>
            <div className="nav-logo-copy">
              <span className="nav-logo-text">
                LUNAR <span>GUARDIANS</span>
              </span>
              <span className="nav-logo-sub">Mission Control</span>
            </div>
          </button>

          <nav className="nav-links" aria-label="Primary navigation">
            {NAV_ITEMS.map((item) => {
              const isActive = item.path
                ? location.pathname === item.path
                : location.pathname === '/' && activeSection === item.target
              return (
                <button
                  key={item.path || item.target}
                  type="button"
                  className={`nav-link${isActive ? ' active' : ''}`}
                  onClick={() => handleNavItem(item)}
                >
                  {item.label}
                </button>
              )
            })}
          </nav>

          <div className="nav-actions">
            <SoundEffects listen={false} />
            <button
              type="button"
              className="nav-cta desktop-only"
              onClick={handleStartMission}
            >
              <Rocket size={15} />
              Start Mission
            </button>

            <button
              type="button"
              className="nav-mobile-btn"
              onClick={() => setMobileOpen(true)}
              aria-label="Open navigation menu"
              aria-expanded={mobileOpen}
            >
              <Menu size={26} />
            </button>
          </div>
        </div>
      </header>

      {/* Mobile responsive navigation drawer */}
      <div
        className={`nav-mobile-overlay${mobileOpen ? ' open' : ''}`}
        onClick={() => setMobileOpen(false)}
        aria-hidden={!mobileOpen}
      >
        <aside
          className="nav-mobile-drawer"
          onClick={(e) => e.stopPropagation()}
          aria-label="Mobile navigation"
        >
          <div className="mobile-drawer-header">
            <span className="nav-logo-text">
              LUNAR <span>GUARDIANS</span>
            </span>
            <button
              type="button"
              className="mobile-close-btn"
              onClick={() => setMobileOpen(false)}
              aria-label="Close navigation menu"
            >
              <X size={24} />
            </button>
          </div>

          <div className="mobile-drawer-links">
            {NAV_ITEMS.map((item) => {
              const isActive = item.path
                ? location.pathname === item.path
                : location.pathname === '/' && activeSection === item.target
              return (
                <button
                  key={item.path || item.target}
                  type="button"
                  className={`nav-link${isActive ? ' active' : ''}`}
                  onClick={() => handleNavItem(item)}
                >
                  {item.label}
                </button>
              )
            })}
          </div>

          <button type="button" className="nav-cta mobile-cta" onClick={handleStartMission}>
            <Rocket size={16} />
            Start Mission
          </button>
          <SoundEffects listen={false} />
        </aside>
      </div>
    </>
  )
}
