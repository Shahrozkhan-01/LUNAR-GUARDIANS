import { lazy, Suspense, useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Rocket,
  Lock,
  CheckCircle2,
  Shield,
  Compass,
  Flame,
  Users,
  Calendar,
  Wind,
  Sun,
  ShieldAlert,
  Sprout,
  AlertTriangle,
  RotateCcw,
  Loader2,
} from 'lucide-react'
import Navbar from '../components/Navbar.jsx'
import Footer from '../components/Footer.jsx'
import { MISSION_BRIEFING_PRESETS } from '../components/nasaMissionBriefingConfig.js'
import {
  useMission,
  DESTINATIONS,
  DIFFICULTIES,
  CREW_OPTIONS,
  DURATION_OPTIONS,
  SETUP_OUTPOST_SYSTEMS,
} from '../context/missionConstants.js'
import './MissionSetup.css'

const NasaMissionBriefing = lazy(() => import('../components/NasaMissionBriefing.jsx'))

const DIFFICULTY_ICONS = {
  explorer: Compass,
  commander: Shield,
  expert: Flame,
}

const SYSTEM_ICONS = {
  'life-support': Wind,
  'solar-power': Sun,
  'radiation-shelter': ShieldAlert,
  greenhouse: Sprout,
}

function MarsLandscapeSvg() {
  return (
    <svg className="dest-mars-svg" viewBox="0 0 480 200" fill="none" aria-hidden="true">
      <defs>
        <linearGradient id="marsSky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#1e0b16" />
          <stop offset="100%" stopColor="#451a14" />
        </linearGradient>
      </defs>
      <rect width="480" height="200" fill="url(#marsSky)" />
      <circle cx="380" cy="48" r="18" fill="#fb923c" opacity="0.28" />
      <circle cx="380" cy="48" r="9" fill="#fdba74" opacity="0.5" />
      <path d="M0 135 L95 92 L175 122 L285 84 L390 118 L480 96 L480 200 L0 200 Z" fill="#5c2118" />
      <path d="M0 155 Q130 132 250 150 T480 142 L480 200 L0 200 Z" fill="#3b130e" />
    </svg>
  )
}

export default function MissionSetup() {
  const navigate = useNavigate()
  const { setupPrefs, startNewMission, isLoadingMission, apiError, clearApiError } = useMission()

  const [destination, setDestination] = useState(() =>
    setupPrefs?.destination || 'lunar-outpost'
  )
  const [difficulty, setDifficulty] = useState(() =>
    setupPrefs?.difficulty || null
  )
  const [crewSize, setCrewSize] = useState(() =>
    setupPrefs?.crewSize || null
  )
  const [duration, setDuration] = useState(() =>
    setupPrefs?.duration || null
  )
  const [nasaBriefingPreset, setNasaBriefingPreset] = useState(() =>
    setupPrefs?.nasaBriefingPreset || MISSION_BRIEFING_PRESETS[0].id
  )
  const [deterministic, setDeterministic] = useState(() =>
    Boolean(setupPrefs?.deterministic)
  )
  const [validationError, setValidationError] = useState('')

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [])

  const selectedDestinationObj = DESTINATIONS.find((d) => d.id === destination)
  const selectedDifficultyObj = DIFFICULTIES.find((d) => d.id === difficulty)

  const handleSelectDifficulty = (id) => {
    setDifficulty(id)
    setValidationError('')
    clearApiError()
  }

  const handleSelectCrew = (count) => {
    setCrewSize(count)
    setValidationError('')
    clearApiError()
  }

  const handleSelectDuration = (days) => {
    setDuration(days)
    setValidationError('')
    clearApiError()
  }

  const handleResetSelections = () => {
    setDestination('lunar-outpost')
    setDifficulty(null)
    setCrewSize(null)
    setDuration(null)
    setDeterministic(false)
    setNasaBriefingPreset(MISSION_BRIEFING_PRESETS[0].id)
    setValidationError('')
    clearApiError()
  }

  const handleInitializeMission = async () => {
    const missing = []
    if (!destination) missing.push('Mission Destination')
    if (!difficulty) missing.push('Difficulty')
    if (!crewSize) missing.push('Crew Selection')
    if (!duration) missing.push('Mission Duration')

    if (missing.length > 0) {
      setValidationError(
        `Commander, please complete all required selections before launch: ${missing.join(', ')}.`
      )
      return
    }

    setValidationError('')
    clearApiError()

    try {
      await startNewMission({
        destination,
        difficulty,
        crewSize,
        duration,
        deterministic,
        nasaBriefingPreset,
      })
      navigate('/mission-control')
    } catch {
      // apiError state in MissionContext already holds the friendly backend message
    }
  }

  return (
    <>
      <Navbar />
      <main className="setup-page">
        <div className="setup-container">
          {/* Page Header */}
          <motion.div
            className="setup-hero-header"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55 }}
          >
            <span className="section-label">Pre-Flight Configuration</span>
            <h1 className="setup-main-title">CONFIGURE YOUR LUNAR MISSION</h1>
            <p className="setup-main-subtitle">
              Choose your destination, difficulty level, astronaut crew size, and mission length
              to launch your authoritative lunar survival simulation.
            </p>
          </motion.div>

          <div className="setup-layout">
            {/* Left / Main Configuration Column */}
            <div className="setup-sections-col">
              {/* SECTION A: MISSION DESTINATION */}
              <section className="setup-block" aria-labelledby="heading-destination">
                <div className="setup-block-header">
                  <span className="setup-step-num">SECTION A</span>
                  <h2 id="heading-destination" className="setup-block-title">
                    Mission Destination
                  </h2>
                </div>

                <div className="destination-grid">
                  {DESTINATIONS.map((dest) => {
                    const isSelected = destination === dest.id
                    const isDisabled = !dest.available

                    return (
                      <button
                        key={dest.id}
                        type="button"
                        disabled={isDisabled}
                        aria-pressed={isSelected}
                        className={`dest-card${isSelected ? ' selected' : ''}${isDisabled ? ' disabled' : ''}`}
                        onClick={() => {
                          if (!isDisabled) {
                            setDestination(dest.id)
                            setValidationError('')
                            clearApiError()
                          }
                        }}
                      >
                        <div className="dest-visual">
                          {dest.id === 'lunar-outpost' ? (
                            <img
                              src="/hero-lunar.png"
                              alt="Moon landscape with lunar habitat and solar panels"
                              className="dest-img"
                            />
                          ) : (
                            <MarsLandscapeSvg />
                          )}
                          <div className="dest-visual-overlay" />
                          <span className={`dest-badge ${dest.available ? 'available' : 'locked'}`}>
                            {dest.available ? <CheckCircle2 size={13} /> : <Lock size={13} />}
                            {dest.status}
                          </span>
                        </div>

                        <div className="dest-body">
                          <span className="dest-subtitle">{dest.subtitle}</span>
                          <h3 className="dest-title">{dest.name}</h3>
                          <p className="dest-desc">{dest.description}</p>
                        </div>
                      </button>
                    )
                  })}
                </div>
              </section>

              {/* SECTION B: DIFFICULTY */}
              <section
                className={`setup-block${validationError && !difficulty ? ' needs-attention' : ''}`}
                aria-labelledby="heading-difficulty"
              >
                <div className="setup-block-header">
                  <span className="setup-step-num">SECTION B</span>
                  <h2 id="heading-difficulty" className="setup-block-title">
                    Select Difficulty
                  </h2>
                </div>

                <div className="three-col-grid">
                  {DIFFICULTIES.map((diff) => {
                    const Icon = DIFFICULTY_ICONS[diff.id] || Shield
                    const isSelected = difficulty === diff.id
                    return (
                      <button
                        key={diff.id}
                        type="button"
                        aria-pressed={isSelected}
                        style={{ '--opt-accent': diff.accent }}
                        className={`option-card${isSelected ? ' selected' : ''}`}
                        onClick={() => handleSelectDifficulty(diff.id)}
                      >
                        <div className="option-card-top">
                          <div className="option-icon-box">
                            <Icon size={22} />
                          </div>
                          {isSelected && (
                            <span className="option-selected-check" aria-hidden="true">
                              <CheckCircle2 size={18} />
                            </span>
                          )}
                        </div>
                        <span className="option-tagline">{diff.tagline}</span>
                        <h3 className="option-title">{diff.name}</h3>
                        <p className="option-desc">{diff.description}</p>
                        <span className="option-meta-pill">
                          {diff.previewText}
                        </span>
                      </button>
                    )
                  })}
                </div>
              </section>

              {/* SECTION C: CREW SELECTION */}
              <section
                className={`setup-block${validationError && !crewSize ? ' needs-attention' : ''}`}
                aria-labelledby="heading-crew"
              >
                <div className="setup-block-header">
                  <span className="setup-step-num">SECTION C</span>
                  <h2 id="heading-crew" className="setup-block-title">
                    Crew Selection
                  </h2>
                </div>

                <div className="three-col-grid">
                  {CREW_OPTIONS.map((crew) => {
                    const isSelected = crewSize === crew.count
                    return (
                      <button
                        key={crew.count}
                        type="button"
                        aria-pressed={isSelected}
                        style={{ '--opt-accent': '#00e5ff' }}
                        className={`option-card compact${isSelected ? ' selected' : ''}`}
                        onClick={() => handleSelectCrew(crew.count)}
                      >
                        <div className="option-card-top">
                          <div className="option-icon-box">
                            <Users size={21} />
                          </div>
                          <div className="crew-dots" aria-hidden="true">
                            {Array.from({ length: crew.count }).map((_, idx) => (
                              <span key={idx} className="crew-mini-dot" />
                            ))}
                          </div>
                        </div>
                        <h3 className="option-title">{crew.label}</h3>
                        <p className="option-desc">{crew.subtitle}</p>
                      </button>
                    )
                  })}
                </div>
              </section>

              {/* SECTION D: MISSION DURATION */}
              <section
                className={`setup-block${validationError && !duration ? ' needs-attention' : ''}`}
                aria-labelledby="heading-duration"
              >
                <div className="setup-block-header">
                  <span className="setup-step-num">SECTION D</span>
                  <h2 id="heading-duration" className="setup-block-title">
                    Mission Duration
                  </h2>
                </div>

                <div className="three-col-grid">
                  {DURATION_OPTIONS.map((dur) => {
                    const isSelected = duration === dur.days
                    return (
                      <button
                        key={dur.days}
                        type="button"
                        aria-pressed={isSelected}
                        style={{ '--opt-accent': '#8b5cf6' }}
                        className={`option-card compact${isSelected ? ' selected' : ''}`}
                        onClick={() => handleSelectDuration(dur.days)}
                      >
                        <div className="option-card-top">
                          <div className="option-icon-box">
                            <Calendar size={21} />
                          </div>
                          {isSelected && (
                            <span className="option-selected-check" aria-hidden="true">
                              <CheckCircle2 size={18} />
                            </span>
                          )}
                        </div>
                        <h3 className="option-title">{dur.label}</h3>
                        <p className="option-desc">{dur.subtitle}</p>
                      </button>
                    )
                  })}
                </div>
              </section>

              {/* SECTION E: OUTPOST SYSTEMS */}
              <section className="setup-block" aria-labelledby="heading-systems">
                <div className="setup-block-header">
                  <span className="setup-step-num">SECTION E</span>
                  <h2 id="heading-systems" className="setup-block-title">
                    Outpost Systems Included
                  </h2>
                </div>

                <div className="setup-systems-grid">
                  {SETUP_OUTPOST_SYSTEMS.map((sys) => {
                    const Icon = SYSTEM_ICONS[sys.id] || Shield
                    return (
                      <div key={sys.id} className="setup-sys-item">
                        <div className="setup-sys-icon">
                          <Icon size={22} />
                        </div>
                        <div className="setup-sys-copy">
                          <div className="setup-sys-title-row">
                            <h3>{sys.name}</h3>
                            <span className="setup-sys-ready">{sys.status}</span>
                          </div>
                          <p>{sys.summary}</p>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </section>

              <Suspense fallback={<div className="setup-block">Loading NASA Mission Briefing…</div>}>
                <NasaMissionBriefing
                  selectedPreset={nasaBriefingPreset}
                  onSelectPreset={setNasaBriefingPreset}
                />
              </Suspense>
            </div>

            {/* Right / Sticky SECTION F: MISSION SUMMARY */}
            <aside className="setup-summary-col" aria-labelledby="heading-summary">
              <div className="summary-panel">
                <div className="summary-header">
                  <span className="setup-step-num">SECTION F</span>
                  <h2 id="heading-summary" className="summary-title">
                    Mission Summary
                  </h2>
                </div>

                <div className="summary-rows">
                  <div className="summary-row">
                    <span className="summary-label">Destination</span>
                    <span className="summary-val">
                      {selectedDestinationObj ? selectedDestinationObj.name : 'Not Selected'}
                    </span>
                  </div>

                  <div className="summary-row">
                    <span className="summary-label">Difficulty</span>
                    <span className={`summary-val${!selectedDifficultyObj ? ' pending' : ''}`}>
                      {selectedDifficultyObj ? selectedDifficultyObj.name : 'Select Difficulty'}
                    </span>
                  </div>

                  <div className="summary-row">
                    <span className="summary-label">Crew Size</span>
                    <span className={`summary-val${!crewSize ? ' pending' : ''}`}>
                      {crewSize ? `${crewSize} Astronauts` : 'Select Crew'}
                    </span>
                  </div>

                  <div className="summary-row">
                    <span className="summary-label">Duration</span>
                    <span className={`summary-val${!duration ? ' pending' : ''}`}>
                      {duration ? `${duration} Days` : 'Select Duration'}
                    </span>
                  </div>

                  <div className="summary-row">
                    <span className="summary-label">NASA Briefing</span>
                    <span className="summary-val">
                      {MISSION_BRIEFING_PRESETS.find((preset) => preset.id === nasaBriefingPreset)?.title || 'South Polar Exploration'}
                    </span>
                  </div>

                  <div className="summary-row">
                    <span className="summary-label">Core Systems</span>
                    <span className="summary-val online">4 / 4 Online</span>
                  </div>
                </div>

                <label className="summary-mode-toggle">
                  <input
                    type="checkbox"
                    checked={deterministic}
                    onChange={(e) => setDeterministic(e.target.checked)}
                  />
                  <div>
                    <strong>Guided Classroom Mode</strong>
                    <span>Use a predictable training event schedule (great for lessons & demos).</span>
                  </div>
                </label>

                <div className="summary-sim-note">
                  <span>SIMULATED GAME UNITS</span>
                  <p>
                    NASA space-weather observations are shown separately when available. Resource values and game consequences remain simulated.
                  </p>
                </div>

                {(validationError || apiError) && (
                  <div className="summary-validation-error" role="alert">
                    <AlertTriangle size={18} />
                    <span>{validationError || apiError}</span>
                  </div>
                )}

                <button
                  type="button"
                  className="btn-initialize-mission"
                  disabled={isLoadingMission}
                  onClick={handleInitializeMission}
                >
                  {isLoadingMission ? (
                    <>
                      <Loader2 size={18} className="spin-icon" />
                      INITIALIZING MISSION...
                    </>
                  ) : (
                    <>
                      <Rocket size={18} />
                      INITIALIZE MISSION
                    </>
                  )}
                </button>

                <button
                  type="button"
                  className="btn-reset-setup"
                  disabled={isLoadingMission}
                  onClick={handleResetSelections}
                >
                  <RotateCcw size={14} />
                  Clear Selections
                </button>
              </div>
            </aside>
          </div>
        </div>
      </main>
      <Footer />
    </>
  )
}
