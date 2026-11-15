import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Wind,
  Droplets,
  Zap,
  Sprout,
  Shield,
  ShieldAlert,
  Radio,
  FastForward,
  RotateCcw,
  SlidersHorizontal,
  Activity,
  Users,
  Sparkles,
  PauseCircle,
  Play,
  AlertTriangle,
  X,
  Lightbulb,
  Trophy,
  Loader2,
  Rocket,
  Wrench,
} from 'lucide-react'
import MissionHeader from '../components/MissionHeader.jsx'
import ResourceCard from '../components/ResourceCard.jsx'
import SystemCard from '../components/SystemCard.jsx'
import SystemModal from '../components/SystemModal.jsx'
import CrewCard from '../components/CrewCard.jsx'
import EventFeed from '../components/EventFeed.jsx'
import PowerAllocationPanel from '../components/PowerAllocationPanel.jsx'
import PlayerActionsPanel from '../components/PlayerActionsPanel.jsx'
import NasaSpaceWeather from '../components/NasaSpaceWeather.jsx'
import NasaTrainingEvents from '../components/NasaTrainingEvents.jsx'
import {
  useMission,
  DIFFICULTIES,
  SYSTEM_MODALS_DATA,
  CREW_VISOR_COLORS,
} from '../context/missionConstants.js'
import './MissionControl.css'

const BASE_SYSTEM_META = [
  {
    id: 'life-support',
    name: 'Life Support',
    code: 'SYS-01',
    icon: Wind,
    accent: '#00e5ff',
  },
  {
    id: 'power-allocation',
    name: 'Power Allocation',
    code: 'SYS-02',
    icon: Zap,
    accent: '#38bdf8',
  },
  {
    id: 'radiation-shelter',
    name: 'Radiation Shelter',
    code: 'SYS-03',
    icon: ShieldAlert,
    accent: '#ff6b35',
  },
  {
    id: 'greenhouse',
    name: 'Greenhouse',
    code: 'SYS-04',
    icon: Sprout,
    accent: '#22c55e',
  },
  {
    id: 'communication',
    name: 'Communication',
    code: 'SYS-05',
    icon: Radio,
    accent: '#a855f7',
  },
]

const OUTPOST_HOTSPOTS = [
  {
    id: 'antenna-pin',
    label: 'Communication Antenna',
    left: '24%',
    top: '18%',
    accent: '#a855f7',
    modalId: 'communication',
  },
  {
    id: 'solar-pin',
    label: 'Solar Panels',
    left: '29%',
    top: '43%',
    accent: '#38bdf8',
    modalId: 'power-allocation',
  },
  {
    id: 'habitat-pin',
    label: 'Lunar Habitat',
    left: '49%',
    top: '54%',
    accent: '#00e5ff',
    modalId: 'life-support',
  },
  {
    id: 'greenhouse-pin',
    label: 'Greenhouse',
    left: '77%',
    top: '46%',
    accent: '#22c55e',
    modalId: 'greenhouse',
  },
  {
    id: 'shelter-pin',
    label: 'Radiation Shelter',
    left: '22%',
    top: '74%',
    accent: '#ff6b35',
    modalId: 'radiation-shelter',
  },
  {
    id: 'astronauts-pin',
    label: 'Astronauts',
    left: '52%',
    top: '84%',
    accent: '#facc15',
    scrollTarget: 'crew-status-section',
  },
]

function getSystemLiveStatus(sysId, gameState) {
  if (!gameState) return 'Simulated: Standby'
  const { power_allocation: pa, subsystems: sub, resources } = gameState
  switch (sysId) {
    case 'life-support':
      return `${Math.round(pa.life_support)} Sim Power • ${
        sub.oxygen_recycling_active ? 'Recycling ON' : 'Base Mode'
      }`
    case 'power-allocation':
      return `Solar ${Math.round(sub.solar_efficiency * 100)}% • ${Math.round(
        resources.power
      )} Units Ready`
    case 'radiation-shelter':
      return `${Math.round(pa.radiation_shelter)} Sim Power • ${
        sub.shelter_boost_days_left > 0
          ? `Boost (${sub.shelter_boost_days_left}d)`
          : 'Shield Online'
      }`
    case 'greenhouse':
      return `${Math.round(pa.greenhouse)} Sim Power • Harvest ${sub.greenhouse_growth_days}/2d`
    case 'communication':
      return `${Math.round(pa.communication)} Sim Power • ${
        pa.communication >= 8 ? 'Telemetry Active' : 'Low Power'
      }`
    default:
      return 'Operational'
  }
}

const DEBRIEF_RESOURCES = [
  ['Oxygen', 'oxygen'],
  ['Water', 'water'],
  ['Power', 'power'],
  ['Food', 'food'],
  ['Shield protection', 'shield'],
]

function buildMissionDebrief(gameState) {
  const lowResources = DEBRIEF_RESOURCES
    .filter(([, key]) => gameState.resources[key] < 35)
    .map(([name]) => name)
  const strengths = []
  if (gameState.mission_status === 'Mission Successful') {
    strengths.push(
      `Completed all ${gameState.duration} mission days with ${gameState.crew_status.general_health.toLowerCase()} crew indicators.`
    )
  } else if (gameState.mission_status === 'Mission Completed with Difficulties') {
    strengths.push(
      `Completed all ${gameState.duration} mission days; final crew indicators were ${gameState.crew_status.general_health.toLowerCase()}.`
    )
  }
  if (gameState.mission_decisions?.length) {
    strengths.push(
      `Made ${gameState.mission_decisions.length} recorded mission decisions or outpost actions.`
    )
  }
  if (!strengths.length) {
    strengths.push('Each choice is a chance to learn and try a different plan next time.')
  }

  const improvements = []
  if (lowResources.length) {
    improvements.push(`Plan earlier for low reserves: ${lowResources.join(', ')}.`)
  }
  if (gameState.crew_status.general_health !== 'Healthy') {
    improvements.push(
      `Review life-support choices to improve the crew indicators, currently ${gameState.crew_status.general_health.toLowerCase()}.`
    )
  }
  if (gameState.mission_status === 'Mission Failed' && gameState.outcome_explanation) {
    improvements.unshift(gameState.outcome_explanation)
  }
  if (!improvements.length) {
    improvements.push(
      'Try a longer mission or a higher difficulty while continuing to balance the outpost systems.'
    )
  }

  const lessons = [...new Set(
    (gameState.mission_decisions || [])
      .map((decision) => decision.lesson)
      .filter(Boolean)
  )].slice(-3)
  if (!lessons.length) {
    lessons.push(
      'Protect essential life-support systems and balance resources throughout the mission.',
      'Mission resources, crew indicators, and Science points are simulated game values, not NASA measurements.'
    )
  }

  return {
    strengths,
    improvements,
    lessons,
    decisions: gameState.mission_decisions || [],
    events: gameState.mission_events || [],
  }
}

export default function MissionControl() {
  const navigate = useNavigate()
  const {
    gameState,
    setupPrefs,
    isPaused,
    isLoadingMission,
    isAdvancingDay,
    pendingActionId,
    isSavingPower,
    apiError,
    feedbackBanner,
    startNewMission,
    advanceDay,
    performAction,
    savePowerAllocation,
    togglePause,
    clearApiError,
  } = useMission()

  const [activeModalId, setActiveModalId] = useState(null)

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [])

  const difficultyObj = useMemo(
    () => DIFFICULTIES.find((d) => d.id === gameState?.difficulty) || DIFFICULTIES[1],
    [gameState?.difficulty]
  )

  // Loading state while hydrating an active mission from the FastAPI backend
  if (isLoadingMission && !gameState) {
    return (
      <div className="mc-page">
        <div className="mc-empty-state">
          <Loader2 size={42} className="mc-spin-icon" />
          <h1>Connecting to Lunar Outpost Simulation...</h1>
          <p>Syncing authoritative telemetry, resources, and crew vitals from Mission Control.</p>
        </div>
      </div>
    )
  }

  // Empty state if no mission has been initialized yet
  if (!gameState) {
    return (
      <div className="mc-page">
        <div className="mc-empty-state">
          <div className="mc-empty-icon-wrap">
            <Rocket size={34} />
          </div>
          <span className="mc-kicker">Lunar Guardians // Simulation Engine</span>
          <h1>No Active Lunar Mission Initialized</h1>
          <p>
            Configure your destination, difficulty, astronaut crew size, and mission duration to
            start a live simulation session on the Mission Control server.
          </p>
          {apiError && (
            <div className="mc-api-error-banner compact" role="alert">
              <AlertTriangle size={18} />
              <span>{apiError}</span>
            </div>
          )}
          <button
            type="button"
            className="btn-next-day mc-empty-launch-btn"
            onClick={() => navigate('/mission-setup')}
          >
            <Rocket size={18} />
            <span>Configure & Launch Mission</span>
          </button>
        </div>
      </div>
    )
  }

  const isMissionOver = gameState.mission_status !== 'In Progress'
  const isBusy = isLoadingMission || isAdvancingDay || Boolean(pendingActionId) || isSavingPower
  const nasaMissionEvents = gameState.active_events.filter(
    (event) => event.source_type === 'NASA'
  )
  const simulatedMissionEvents = gameState.active_events.filter(
    (event) => event.source_type !== 'NASA'
  )

  const resourceCards = [
    {
      name: 'Oxygen',
      icon: Wind,
      value: gameState.resources.oxygen,
      accentColor: '#00e5ff',
    },
    {
      name: 'Water',
      icon: Droplets,
      value: gameState.resources.water,
      accentColor: '#38bdf8',
    },
    {
      name: 'Power',
      icon: Zap,
      value: gameState.resources.power,
      accentColor: '#facc15',
    },
    {
      name: 'Food',
      icon: Sprout,
      value: gameState.resources.food,
      accentColor: '#22c55e',
    },
    {
      name: 'Shield Protection',
      icon: Shield,
      value: gameState.resources.shield,
      accentColor: '#a855f7',
    },
  ]

  const activeModalData = activeModalId ? SYSTEM_MODALS_DATA[activeModalId] : null
  const activeModalBtn = BASE_SYSTEM_META.find((s) => s.id === activeModalId)

  const handleHotspotClick = (spot) => {
    if (spot.modalId) {
      setActiveModalId(spot.modalId)
    } else if (spot.scrollTarget) {
      const el = document.getElementById(spot.scrollTarget)
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  const handleRelaunchSameSetup = async () => {
    try {
      await startNewMission({
        destination: gameState.destination || setupPrefs?.destination || 'lunar-outpost',
        difficulty: gameState.difficulty,
        crewSize: gameState.crew_size,
        duration: gameState.duration,
        deterministic: gameState.deterministic,
        enableRandomEvents: gameState.enable_random_events,
        nasaBriefingPreset: setupPrefs?.nasaBriefingPreset,
      })
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } catch {
      // apiError handled in MissionContext
    }
  }

  const outcomeTone =
    gameState.mission_status === 'Mission Successful'
      ? 'success'
      : gameState.mission_status === 'Mission Completed with Difficulties'
      ? 'partial'
      : 'failed'
  const missionDebrief = isMissionOver ? buildMissionDebrief(gameState) : null

  return (
    <div className="mc-page">
      {/* SECTION A: TOP NAVIGATION */}
      <MissionHeader
        missionName={gameState.mission_name}
        difficultyLabel={difficultyObj.name}
        currentDay={gameState.current_day}
        duration={gameState.duration}
        sciencePoints={gameState.science_points}
        missionStatus={gameState.mission_status}
        isPaused={isPaused}
        onTogglePause={togglePause}
      />

      <main className="mc-main">
        {/* Simulation & NASA Status Ribbon */}
        <div className="mc-disclaimer-bar">
          <div className="mc-disclaimer-badges">
            <span className="mc-tag-sim">SIMULATED GAME UNITS</span>
            <span className="mc-tag-nasa">REAL NASA DATA: DONKI</span>
          </div>
          <p className="mc-disclaimer-text">
            NASA observations are real. Resource balances, crew indicators, and all gameplay consequences are simulated game models.
          </p>
        </div>

        <NasaSpaceWeather />

        {/* Dismissible API / Validation Error Alert */}
        {apiError && (
          <div className="mc-api-error-banner" role="alert">
            <div className="mc-api-error-left">
              <AlertTriangle size={20} />
              <div>
                <strong>Command Notice</strong>
                <span>{apiError}</span>
              </div>
            </div>
            <button
              type="button"
              className="mc-dismiss-btn"
              onClick={clearApiError}
              aria-label="Dismiss alert"
            >
              <X size={16} />
            </button>
          </div>
        )}

        <section className="mc-panel" aria-labelledby="mc-nasa-alerts-heading">
          <div className="mc-panel-header">
            <div>
              <span className="mc-kicker">Mission decisions from real observations</span>
              <h2 id="mc-nasa-alerts-heading" className="mc-panel-title">
                NASA Space Weather Alerts
              </h2>
            </div>
            <span className="mc-sim-label-pill">
              {nasaMissionEvents.length > 0
                ? `${nasaMissionEvents.length} ACTIVE`
                : 'NO ACTIVE NASA ALERT'}
            </span>
          </div>
          <EventFeed
            activeEvents={nasaMissionEvents}
            disabled={isPaused || isMissionOver}
            pendingAction={Boolean(pendingActionId)}
            showOperationalStatus={false}
            emptyMessage="No NASA-informed mission alert is active. Real observations and their availability are shown in the NASA monitor above. Your mission remains playable."
            onResolveEvent={(eventId, choiceId) =>
              performAction('resolve_event', { event_id: eventId, choice_id: choiceId })
            }
          />
        </section>

        <section className="mc-panel" aria-labelledby="mc-nasa-training-heading">
          <div className="mc-panel-header">
            <div>
              <span className="mc-kicker">Optional, NASA-informed learning scenarios</span>
              <h2 id="mc-nasa-training-heading" className="mc-panel-title">
                NASA Training Events
              </h2>
            </div>
            <span className="mc-sim-label-pill">SIMULATED TRAINING EVENTS</span>
          </div>
          <p className="nasa-training-intro">
            NASA observations and computed ephemerides are shown with their dates and
            limitations. Player choices affect only simulated game indicators and do
            not change mission resources until a choice is selected.
          </p>
          <NasaTrainingEvents
            events={gameState.nasa_training_events || []}
            resources={gameState.resources}
            disabled={isPaused || isMissionOver}
            pendingAction={Boolean(pendingActionId)}
            onResolveEvent={(eventId, choiceId) =>
              performAction('resolve_nasa_training_event', {
                event_id: eventId,
                choice_id: choiceId,
              })
            }
          />
        </section>

        {/* Mission Outcome Debrief Banner */}
        {isMissionOver && (
          <motion.section
            className={`mc-outcome-banner ${outcomeTone}`}
            initial={{ opacity: 0, y: -12 }}
            animate={{ opacity: 1, y: 0 }}
            aria-labelledby="mc-outcome-heading"
          >
            <div className="mc-outcome-main">
              <div className="mc-outcome-icon">
                {outcomeTone === 'failed' ? <AlertTriangle size={28} /> : <Trophy size={28} />}
              </div>
              <div className="mc-outcome-copy">
                <span className="mc-outcome-kicker">Mission Debrief // Final Status</span>
                <h2 id="mc-outcome-heading">{gameState.mission_status}</h2>
                <p>{gameState.outcome_explanation}</p>
                <div className="mc-outcome-stats">
                  <span>Final Day: {gameState.current_day} / {gameState.duration}</span>
                  <span>SIMULATED SCIENCE SCORE: {gameState.science_points} PTS</span>
                  <span>Crew Condition: {gameState.crew_status.general_health}</span>
                </div>
              </div>
            </div>

            <section className="mc-outcome-report" aria-label="Final mission report">
              <div className="mc-report-score">
                <span>SIMULATED SCIENCE POINTS // GAME SCORE</span>
                <strong>{gameState.science_points}</strong>
                <small>Practice points earned during this mission</small>
              </div>

              <div className="mc-report-section">
                <h3>Final resource levels</h3>
                <div className="mc-report-resources">
                  {DEBRIEF_RESOURCES.map(([name, key]) => (
                    <span key={key}>
                      {name}: <strong>{gameState.resources[key]} / 100</strong>
                    </span>
                  ))}
                </div>
                <small>All resource amounts are simulated game units.</small>
              </div>

              <div className="mc-report-feedback">
                <div className="mc-report-section">
                  <h3>What went well</h3>
                  <ul>{missionDebrief.strengths.map((item) => <li key={item}>{item}</li>)}</ul>
                </div>
                <div className="mc-report-section">
                  <h3>What could improve</h3>
                  <ul>{missionDebrief.improvements.map((item) => <li key={item}>{item}</li>)}</ul>
                </div>
              </div>

              <div className="mc-report-section">
                <h3>Learning takeaways</h3>
                <ul>{missionDebrief.lessons.map((item) => <li key={item}>{item}</li>)}</ul>
              </div>

              <div className="mc-report-history">
                <div className="mc-report-section">
                  <h3>
                    Important decisions
                    {missionDebrief.decisions.length > 6 && (
                      <span> (showing latest 6 of {missionDebrief.decisions.length})</span>
                    )}
                  </h3>
                  {missionDebrief.decisions.length ? (
                    <ul>
                      {missionDebrief.decisions.slice(-6).reverse().map((decision, index) => (
                        <li key={`${decision.day}-${decision.subject}-${index}`}>
                          <span className="mc-report-source-label">{decision.source_label}</span>
                          <strong>Day {decision.day}: {decision.subject}</strong>
                          <span>Choice: {decision.choice}</span>
                          <span>
                            {decision.consequence_label}:{' '}
                            {decision.consequence.replace(
                              /^SIMULATED GAME CONSEQUENCE:\s*/i,
                              ''
                            )}
                          </span>
                        </li>
                      ))}
                    </ul>
                  ) : <p>No player decisions were recorded.</p>}
                </div>

                <div className="mc-report-section">
                  <h3>
                    Major events encountered
                    {missionDebrief.events.length > 6 && (
                      <span> (showing latest 6 of {missionDebrief.events.length})</span>
                    )}
                  </h3>
                  {missionDebrief.events.length ? (
                    <ul>
                      {missionDebrief.events.slice(-6).reverse().map((event, index) => (
                        <li key={`${event.day}-${event.title}-${index}`}>
                          <span className="mc-report-source-label">{event.source_label}</span>
                          <strong>Day {event.day}: {event.title}</strong>
                          <span>{event.description}</span>
                        </li>
                      ))}
                    </ul>
                  ) : <p>No major mission events were recorded.</p>}
                </div>
              </div>
            </section>

            <div className="mc-outcome-actions">
              <button
                type="button"
                className="btn-next-day"
                disabled={isBusy}
                onClick={handleRelaunchSameSetup}
              >
                <RotateCcw size={17} />
                <span>Relaunch Same Mission</span>
              </button>
              <button
                type="button"
                className="btn-reconfigure-mission"
                onClick={() => navigate('/mission-setup')}
              >
                <Sparkles size={16} />
                <span>Configure New Mission</span>
              </button>
            </div>
          </motion.section>
        )}

        {/* Friendly Educational Feedback Banner */}
        {feedbackBanner && !isMissionOver && (
          <div className={`mc-feedback-banner tone-${feedbackBanner.tone || 'info'}`}>
            <div className="mc-feedback-main">
              <Lightbulb size={20} className="mc-feedback-icon" />
              <div>
                <strong>{feedbackBanner.title}:</strong>{' '}
                <span>{feedbackBanner.message}</span>
                {feedbackBanner.educational && (
                  <p className="mc-feedback-edu">
                    Junior Astronaut Tip: {feedbackBanner.educational}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Pause Banner */}
        {isPaused && (
          <motion.div
            className="mc-paused-banner"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="mc-paused-left">
              <PauseCircle size={22} />
              <div>
                <strong>MISSION PAUSED</strong>
                <span>
                  Simulation clock is holding on Day {gameState.current_day}. Resume to execute actions or advance to the next day.
                </span>
              </div>
            </div>
            <div className="mc-paused-actions">
              <button type="button" className="mc-resume-inline-btn" onClick={togglePause}>
                <Play size={15} />
                Resume Mission
              </button>
              <button
                type="button"
                className="mc-reconfig-inline-btn"
                onClick={() => navigate('/mission-setup')}
              >
                <SlidersHorizontal size={15} />
                Reconfigure Setup
              </button>
            </div>
          </motion.div>
        )}

        {/* SECTION B: RESOURCE MONITORING */}
        <section className="mc-section" aria-labelledby="mc-resources-heading">
          <div className="mc-section-header">
            <div>
              <span className="mc-kicker">Telemetry Readout</span>
              <h2 id="mc-resources-heading" className="mc-section-title">
                Resource Monitoring
              </h2>
            </div>
            <span className="mc-sim-label-pill">SIMULATED GAME UNITS</span>
          </div>

          <div className="mc-resources-grid">
            {resourceCards.map((res, idx) => (
              <ResourceCard
                key={res.name}
                index={idx}
                icon={res.icon}
                name={res.name}
                value={res.value}
                accentColor={res.accentColor}
              />
            ))}
          </div>
        </section>

        {/* CENTER GRID: SECTION C (OUTPOST VISUALIZATION) + SECTION E (SYSTEM MANAGEMENT + NEXT DAY) */}
        <div className="mc-primary-grid">
          {/* SECTION C: OUTPOST VISUALIZATION */}
          <section className="mc-panel mc-outpost-panel" aria-labelledby="mc-outpost-heading">
            <div className="mc-panel-header">
              <div>
                <span className="mc-kicker">Surface Camera // Sector 01</span>
                <h2 id="mc-outpost-heading" className="mc-panel-title">
                  Lunar Outpost Visualization
                </h2>
              </div>
              <span className="mc-hint-chip">Click any module pin to inspect</span>
            </div>

            <div className="outpost-viewport">
              <img
                src="/outpost-overview.png"
                alt="Panoramic lunar outpost showing habitat dome, solar panels, greenhouse, communication antenna, radiation shelter, and astronauts"
                className="outpost-image"
              />
              <div className="outpost-vignette" aria-hidden="true" />

              {OUTPOST_HOTSPOTS.map((spot) => (
                <button
                  key={spot.id}
                  type="button"
                  className="outpost-hotspot"
                  style={{
                    left: spot.left,
                    top: spot.top,
                    '--pin-color': spot.accent,
                  }}
                  onClick={() => handleHotspotClick(spot)}
                >
                  <span className="hotspot-ping" aria-hidden="true" />
                  <span className="hotspot-dot" aria-hidden="true" />
                  <span className="hotspot-label">{spot.label}</span>
                </button>
              ))}
            </div>

            {/* Accessible Module Legend Strip */}
            <div className="outpost-legend">
              {OUTPOST_HOTSPOTS.map((spot) => (
                <button
                  key={`${spot.id}-legend`}
                  type="button"
                  className="outpost-legend-chip"
                  style={{ '--pin-color': spot.accent }}
                  onClick={() => handleHotspotClick(spot)}
                >
                  <span className="legend-dot" aria-hidden="true" />
                  {spot.label}
                </button>
              ))}
            </div>
          </section>

          {/* SECTION E: SYSTEM MANAGEMENT + SECTION H: NEXT DAY COMMAND */}
          <div className="mc-side-stack">
            <section className="mc-panel" aria-labelledby="mc-systems-heading">
              <div className="mc-panel-header">
                <div>
                  <span className="mc-kicker">Module Inspection</span>
                  <h2 id="mc-systems-heading" className="mc-panel-title">
                    System Guides
                  </h2>
                </div>
              </div>

              <div className="mc-systems-list">
                {BASE_SYSTEM_META.map((sys, idx) => (
                  <SystemCard
                    key={sys.id}
                    index={idx}
                    icon={sys.icon}
                    name={sys.name}
                    code={sys.code}
                    statusText={getSystemLiveStatus(sys.id, gameState)}
                    accentColor={sys.accent}
                    onClick={() => setActiveModalId(sys.id)}
                  />
                ))}
              </div>
            </section>

            {/* SECTION H: NEXT DAY BUTTON */}
            <section className="mc-panel mc-nextday-panel" aria-labelledby="mc-nextday-heading">
              <div className="mc-nextday-copy">
                <span className="mc-kicker">Timeline Control</span>
                <h2 id="mc-nextday-heading" className="mc-panel-title">
                  {isMissionOver
                    ? gameState.mission_status
                    : `Advance from Day ${gameState.current_day}`}
                </h2>
                <p>
                  {isMissionOver
                    ? `Simulation ended on Day ${gameState.current_day} of ${gameState.duration}. Review your debrief or launch another expedition!`
                    : gameState.active_events.length > 0
                    ? `${gameState.active_events.length} active training event(s) awaiting your decision below before advancing!`
                    : `Ready for the next lunar rotation? Advance to calculate daily solar power, recycling, crops, and crew consumption.`}
                </p>
              </div>

              {!isMissionOver ? (
                <button
                  type="button"
                  className="btn-next-day"
                  disabled={isPaused || isBusy}
                  onClick={advanceDay}
                >
                  {isAdvancingDay ? (
                    <>
                      <Loader2 size={20} className="mc-spin-icon" />
                      <span>ADVANCING DAY...</span>
                    </>
                  ) : (
                    <>
                      <FastForward size={20} />
                      <span>{isPaused ? 'MISSION PAUSED' : 'NEXT DAY'}</span>
                    </>
                  )}
                </button>
              ) : (
                <div className="mc-complete-actions">
                  <button
                    type="button"
                    className="btn-next-day"
                    disabled={isBusy}
                    onClick={handleRelaunchSameSetup}
                  >
                    <RotateCcw size={18} />
                    <span>Relaunch Day 1</span>
                  </button>
                  <button
                    type="button"
                    className="btn-reconfigure-mission"
                    onClick={() => navigate('/mission-setup')}
                  >
                    <Sparkles size={16} />
                    <span>New Mission Setup</span>
                  </button>
                </div>
              )}
            </section>
          </div>
        </div>

        {/* GAMEPLAY COMMANDS: POWER ALLOCATION + PLAYER ACTIONS */}
        <div className="mc-commands-grid">
          {/* POWER ALLOCATION PANEL */}
          <section className="mc-panel" aria-labelledby="mc-power-heading">
            <div className="mc-panel-header">
              <div>
                <span className="mc-kicker">Electrical Distribution // Priority Grid</span>
                <h2 id="mc-power-heading" className="mc-panel-title">
                  Power Allocation
                </h2>
              </div>
              <span className="mc-sim-label-pill">MAX = AVAILABLE POWER</span>
            </div>

            <PowerAllocationPanel
              availablePower={gameState.resources.power}
              powerAllocation={gameState.power_allocation}
              solarEfficiency={gameState.subsystems.solar_efficiency}
              conservationDays={gameState.subsystems.conservation_mode_days_left}
              disabled={isPaused || isMissionOver}
              isSaving={isSavingPower}
              onApplyPower={savePowerAllocation}
            />
          </section>

          {/* PLAYER ACTIONS PANEL */}
          <section className="mc-panel" aria-labelledby="mc-actions-heading">
            <div className="mc-panel-header">
              <div>
                <span className="mc-kicker">Outpost Operations // Trade-Offs & Boosts</span>
                <h2 id="mc-actions-heading" className="mc-panel-title">
                  Commander Actions
                </h2>
              </div>
              <Wrench size={18} className="mc-header-accent-icon" />
            </div>

            <PlayerActionsPanel
              actions={gameState.available_actions}
              resources={gameState.resources}
              subsystems={gameState.subsystems}
              disabled={isPaused || isMissionOver}
              pendingActionId={pendingActionId}
              onExecuteAction={(actionId) => performAction(actionId)}
            />
          </section>
        </div>

        {/* LOWER GRID: SECTION D (MISSION EVENTS) + SECTION G (ACTIVITY LOG) */}
        <div className="mc-secondary-grid">
          {/* SECTION D: MISSION EVENTS */}
          <section className="mc-panel" aria-labelledby="mc-events-heading">
            <div className="mc-panel-header">
              <div>
                <span className="mc-kicker">Training Alerts & Decisions</span>
                <h2 id="mc-events-heading" className="mc-panel-title">
                  Mission Events
                </h2>
              </div>
              <span className="mc-sim-label-pill">
                {simulatedMissionEvents.length > 0
                  ? `${simulatedMissionEvents.length} ACTIVE`
                  : 'ALL CLEAR'}
              </span>
            </div>

            <EventFeed
              activeEvents={simulatedMissionEvents}
              subsystems={gameState.subsystems}
              crewHealth={gameState.crew_status.general_health}
              disabled={isPaused || isMissionOver}
              pendingAction={Boolean(pendingActionId)}
              onResolveEvent={(eventId, choiceId) =>
                performAction('resolve_event', { event_id: eventId, choice_id: choiceId })
              }
            />
          </section>

          {/* SECTION G: MISSION ACTIVITY LOG */}
          <section className="mc-panel" aria-labelledby="mc-log-heading">
            <div className="mc-panel-header">
              <div>
                <span className="mc-kicker">Chronological Record</span>
                <h2 id="mc-log-heading" className="mc-panel-title">
                  Mission Activity Log
                </h2>
              </div>
              <Activity size={18} className="mc-header-accent-icon" />
            </div>

            <div className="mc-activity-log">
              {gameState.activity_log.map((entry) => (
                <div key={entry.id} className={`mc-log-entry cat-${entry.category || 'info'}`}>
                  <span className="mc-log-day">DAY {entry.day}</span>
                  <p className="mc-log-msg">{entry.message}</p>
                </div>
              ))}
            </div>
          </section>
        </div>

        {/* SECTION F: CREW STATUS & EDUCATIONAL SCIENCE NOTES */}
        <section
          className="mc-panel mc-crew-section"
          id="crew-status-section"
          aria-labelledby="mc-crew-heading"
        >
          <div className="mc-panel-header">
            <div>
              <span className="mc-kicker">
                Astronaut Roster ({gameState.crew_size} Crew Members)
              </span>
              <h2 id="mc-crew-heading" className="mc-panel-title">
                Crew Status & Life-Support Indicators
              </h2>
            </div>
            <div className="mc-crew-badges">
              <span
                className={`mc-crew-health-pill health-${gameState.crew_status.general_health.toLowerCase()}`}
              >
                Overall: {gameState.crew_status.general_health}
              </span>
              <span className="mc-crew-count-pill">
                <Users size={14} />
                {gameState.crew_size} Astronauts
              </span>
              <span className="mc-sim-label-pill">SIMULATED GAME INDICATORS</span>
            </div>
          </div>

          {/* Crew Availability & Simulated Radiation Summary Strip */}
          <div className="mc-crew-vitals-strip">
            <div className="mc-vital-chip">
              <span>Oxygen Supply</span>
              <strong>{gameState.crew_status.oxygen_availability}</strong>
            </div>
            <div className="mc-vital-chip">
              <span>Water Supply</span>
              <strong>{gameState.crew_status.water_availability}</strong>
            </div>
            <div className="mc-vital-chip">
              <span>Food Rations</span>
              <strong>{gameState.crew_status.food_availability}</strong>
            </div>
            <div className="mc-vital-chip">
              <span>Simulated Radiation Exposure</span>
              <strong>
                {gameState.crew_status.radiation_level} ({gameState.crew_status.radiation_exposure}%)
              </strong>
            </div>
          </div>

          {/* Kid-Friendly Educational Crew & Mission Explanations */}
          {(gameState.crew_status.educational_explanations?.length > 0 ||
            gameState.educational_tips?.length > 0) && (
            <div className="mc-crew-edu-box">
              {gameState.crew_status.educational_explanations?.map((note, i) => (
                <p key={`crew-edu-${i}`}>
                  <Lightbulb size={15} />
                  <span>{note}</span>
                </p>
              ))}
              {gameState.educational_tips?.slice(0, 2).map((tip, i) => (
                <p key={`tip-edu-${i}`} className="mc-tip-secondary">
                  <Sparkles size={15} />
                  <span>{tip}</span>
                </p>
              ))}
            </div>
          )}

          <div className="mc-crew-grid">
            {gameState.crew_status.members.map((member, idx) => (
              <CrewCard
                key={member.id}
                index={idx}
                numberLabel={member.name}
                role={member.role}
                condition={member.condition}
                visorColor={CREW_VISOR_COLORS[idx % CREW_VISOR_COLORS.length]}
              />
            ))}
          </div>
        </section>
      </main>

      {/* Informative System Modal */}
      <SystemModal
        system={activeModalData}
        icon={activeModalBtn?.icon}
        onClose={() => setActiveModalId(null)}
      />
    </div>
  )
}
