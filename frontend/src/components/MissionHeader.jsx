import { useNavigate } from 'react-router-dom'
import { Moon, Pause, Play, SlidersHorizontal, Home, FlaskConical, Database } from 'lucide-react'
import './MissionHeader.css'
import SoundEffects from './SoundEffects.jsx'

export default function MissionHeader({
  missionName,
  difficultyLabel,
  currentDay,
  duration,
  sciencePoints = 0,
  missionStatus = 'In Progress',
  isPaused,
  onTogglePause,
}) {
  const navigate = useNavigate()
  const progressPct = Math.min(100, Math.round((currentDay / duration) * 100))

  return (
    <header className="mc-header">
      <div className="mc-header-inner">
        {/* Brand + Mission Name */}
        <div className="mc-brand-group">
          <button
            type="button"
            className="mc-logo-btn"
            onClick={() => navigate('/')}
            title="Return to Landing Page"
          >
            <div className="mc-logo-icon">
              <Moon size={18} strokeWidth={2.4} />
            </div>
            <div className="mc-logo-text-wrap">
              <span className="mc-logo-title">
                LUNAR <span>GUARDIANS</span>
              </span>
              <span className="mc-sim-pill">SIMULATED GAME UNITS</span>
            </div>
          </button>

          <div className="mc-divider" aria-hidden="true" />

          <div className="mc-mission-meta">
            <span className="mc-mission-label">{missionStatus}</span>
            <div className="mc-mission-name-row">
              <h1 className="mc-mission-name">{missionName}</h1>
              <span className="mc-difficulty-chip">{difficultyLabel}</span>
            </div>
          </div>
        </div>

        {/* Day, Progress & Science Points */}
        <div className="mc-progress-group">
          <div className="mc-day-readout">
            <span className="mc-day-label">Mission Day</span>
            <span className="mc-day-value">
              DAY <strong>{currentDay}</strong> <span>/ {duration}</span>
            </span>
          </div>

          <div className="mc-progress-bar-wrap">
            <div className="mc-progress-top">
              <span>Mission Progress</span>
              <span className="mc-progress-pct">{progressPct}%</span>
            </div>
            <div
              className="mc-progress-track"
              role="progressbar"
              aria-valuenow={progressPct}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label="Mission progress"
            >
              <div
                className="mc-progress-fill"
                style={{ width: `${progressPct}%` }}
              />
            </div>
          </div>

          <div className="mc-science-badge" title="Earned Science Points">
            <FlaskConical size={16} />
            <div>
              <span className="mc-science-label">Science</span>
              <strong className="mc-science-val">{sciencePoints} PTS</strong>
            </div>
          </div>
        </div>

        {/* Controls */}
        <div className="mc-controls-group">
          <SoundEffects listen={false} />
          <button
            type="button"
            className="mc-nav-icon-btn"
            onClick={() => navigate('/nasa-data')}
            title="Open NASA Data Explorer"
            aria-label="NASA Data Explorer"
          >
            <Database size={16} />
            <span className="mc-btn-hide-sm">NASA Data</span>
          </button>
          <button
            type="button"
            className="mc-nav-icon-btn"
            onClick={() => navigate('/mission-setup')}
            title="New Mission Setup"
            aria-label="Configure Mission Setup"
          >
            <SlidersHorizontal size={16} />
            <span className="mc-btn-hide-sm">Setup</span>
          </button>

          <button
            type="button"
            className="mc-nav-icon-btn"
            onClick={() => navigate('/')}
            title="Exit to Home"
            aria-label="Return to Home Page"
          >
            <Home size={16} />
          </button>

          <button
            type="button"
            className={`mc-pause-btn${isPaused ? ' paused' : ''}`}
            onClick={onTogglePause}
          >
            {isPaused ? <Play size={16} /> : <Pause size={16} />}
            <span>{isPaused ? 'Resume' : 'Pause'}</span>
          </button>
        </div>
      </div>
    </header>
  )
}
