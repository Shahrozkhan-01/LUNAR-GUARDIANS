import {
  Wind,
  Droplets,
  Sprout,
  ShieldAlert,
  FlaskConical,
  BatteryCharging,
  Wrench,
  Play,
  Clock,
} from 'lucide-react'
import './PlayerActionsPanel.css'

const ACTION_ICONS = {
  activate_oxygen_recycling: Wind,
  activate_water_recovery: Droplets,
  activate_greenhouse: Sprout,
  activate_radiation_shelter: ShieldAlert,
  start_scientific_research: FlaskConical,
  emergency_conservation_mode: BatteryCharging,
  repair_solar_panels: Wrench,
}

function formatCost(costObj) {
  const entries = Object.entries(costObj || {}).filter(([, v]) => v > 0)
  if (entries.length === 0) return '0 Resources (Immediate Protocol)'
  return entries.map(([k, v]) => `${v} ${k.charAt(0).toUpperCase() + k.slice(1)}`).join(' + ')
}

function canAffordAction(costObj, resources, actionId, subsystems) {
  if (actionId === 'start_scientific_research' && subsystems?.conservation_mode_days_left > 0) {
    return { affordable: false, reason: 'Blocked during Conservation Mode' }
  }
  for (const [k, amount] of Object.entries(costObj || {})) {
    if ((resources?.[k] ?? 0) < amount) {
      return { affordable: false, reason: `Needs ${amount} ${k}` }
    }
  }
  return { affordable: true, reason: '' }
}

function getSubsystemBadge(actionId, subsystems) {
  if (!subsystems) return null
  switch (actionId) {
    case 'activate_oxygen_recycling':
      return subsystems.oxygen_recycling_active ? 'Recycling: ON' : 'Recycling: OFF'
    case 'activate_water_recovery':
      return subsystems.water_recovery_active ? 'Recovery: ON' : 'Recovery: OFF'
    case 'activate_greenhouse':
      return subsystems.greenhouse_active
        ? `Harvest Cycle: ${subsystems.greenhouse_growth_days}/2 Days`
        : 'Greenhouse: OFF'
    case 'activate_radiation_shelter':
      return subsystems.shelter_boost_days_left > 0
        ? `Boost Active: ${subsystems.shelter_boost_days_left}d`
        : 'Standby'
    case 'start_scientific_research':
      return subsystems.research_days_left > 0
        ? `Lab Active: ${subsystems.research_days_left}d`
        : 'Lab Idle'
    case 'emergency_conservation_mode':
      return subsystems.conservation_mode_days_left > 0
        ? `Active: ${subsystems.conservation_mode_days_left}d left`
        : 'Standby'
    case 'repair_solar_panels':
      return `Solar Eff: ${Math.round((subsystems.solar_efficiency || 1) * 100)}%`
    default:
      return null
  }
}

export default function PlayerActionsPanel({
  actions = [],
  resources,
  subsystems,
  disabled = false,
  pendingActionId = null,
  onExecuteAction,
}) {
  return (
    <div className="actions-grid">
      {actions.map((action) => {
        const Icon = ACTION_ICONS[action.id] || Play
        const { affordable, reason } = canAffordAction(
          action.cost,
          resources,
          action.id,
          subsystems
        )
        const badgeText = getSubsystemBadge(action.id, subsystems)
        const isRunning = pendingActionId === action.id

        return (
          <article key={action.id} className="player-action-card">
            <div className="player-action-top">
              <div className="player-action-title-wrap">
                <div className="player-action-icon">
                  <Icon size={19} />
                </div>
                <h3 className="player-action-name">{action.name}</h3>
              </div>

              {badgeText && <span className="player-action-state-pill">{badgeText}</span>}
            </div>

            <p className="player-action-desc">{action.description}</p>

            <div className="player-action-meta">
              <span className="action-cost-tag">Cost: {formatCost(action.cost)}</span>
              {action.duration_days && (
                <span className="action-duration-tag">
                  <Clock size={12} />
                  {action.duration_days} Days
                </span>
              )}
            </div>

            <p className="player-action-benefit">
              <strong>Expected Benefit:</strong> {action.benefit_summary}
            </p>

            <button
              type="button"
              className="btn-execute-action"
              disabled={disabled || Boolean(pendingActionId) || !affordable}
              onClick={() => onExecuteAction(action.id)}
            >
              <Play size={14} />
              <span>
                {isRunning
                  ? 'Executing...'
                  : !affordable
                  ? reason
                  : 'Execute Action'}
              </span>
            </button>
          </article>
        )
      })}
    </div>
  )
}
