import { useState } from 'react'
import { Zap, Wind, ShieldAlert, Sprout, Radio, FlaskConical, AlertCircle } from 'lucide-react'
import './PowerAllocationPanel.css'

const POWER_SYSTEMS = [
  {
    key: 'life_support',
    label: 'Life Support',
    priority: 'Priority #1 (Essential)',
    icon: Wind,
    accent: '#00e5ff',
    minRecommended: 15,
    lowWarning: 'Below 15 units: Oxygen & Water Recycling will shut off!',
  },
  {
    key: 'radiation_shelter',
    label: 'Radiation Shelter',
    priority: 'Priority #2 (Protection)',
    icon: ShieldAlert,
    accent: '#ff6b35',
    minRecommended: 12,
    lowWarning: 'Below 12 units: Shield Protection will slowly decay.',
  },
  {
    key: 'greenhouse',
    label: 'Greenhouse',
    priority: 'Priority #3 (Food Crops)',
    icon: Sprout,
    accent: '#22c55e',
    minRecommended: 12,
    lowWarning: 'Below 12 units: Grow-lights pause crop production.',
  },
  {
    key: 'communication',
    label: 'Communication',
    priority: 'Priority #4 (Telemetry)',
    icon: Radio,
    accent: '#a855f7',
    minRecommended: 8,
    lowWarning: 'Below 8 units: Daily telemetry Science bonus pauses.',
  },
  {
    key: 'scientific_research',
    label: 'Scientific Research',
    priority: 'Priority #5 (Lab)',
    icon: FlaskConical,
    accent: '#38bdf8',
    minRecommended: 10,
    lowWarning: 'Needs 10+ units to generate daily research Science Points.',
  },
]

export default function PowerAllocationPanel({
  availablePower,
  powerAllocation,
  solarEfficiency = 1.0,
  conservationDays = 0,
  disabled = false,
  isSaving = false,
  onApplyPower,
}) {
  const propSignature = [
    powerAllocation.life_support,
    powerAllocation.radiation_shelter,
    powerAllocation.greenhouse,
    powerAllocation.communication,
    powerAllocation.scientific_research,
  ].join('|')

  const [editState, setEditState] = useState({
    signature: propSignature,
    values: powerAllocation,
  })

  const draft = editState.signature === propSignature ? editState.values : powerAllocation

  const maxBudget = Math.floor(availablePower)
  const totalAllocated = Math.round(
    draft.life_support +
      draft.radiation_shelter +
      draft.greenhouse +
      draft.communication +
      draft.scientific_research
  )
  const unallocated = Math.max(0, Math.round(availablePower - totalAllocated))

  const hasChanges = POWER_SYSTEMS.some(
    (s) => Math.round(draft[s.key]) !== Math.round(powerAllocation[s.key])
  )

  const handleSliderChange = (sysKey, rawValue) => {
    const requested = Math.max(0, Number(rawValue))
    const othersSum = POWER_SYSTEMS.reduce(
      (acc, s) => (s.key === sysKey ? acc : acc + draft[s.key]),
      0
    )
    const maxAllowedForThis = Math.max(0, Math.floor(availablePower - othersSum))
    const clamped = Math.min(requested, maxAllowedForThis)
    setEditState({
      signature: propSignature,
      values: {
        ...draft,
        [sysKey]: clamped,
      },
    })
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    onApplyPower(draft)
  }

  return (
    <form className="power-panel" onSubmit={handleSubmit}>
      <div className="power-budget-bar">
        <div className="power-budget-item">
          <span className="power-budget-label">Available Electricity</span>
          <strong className="power-budget-val cyan">{availablePower} Units</strong>
        </div>
        <div className="power-budget-item">
          <span className="power-budget-label">Allocated Total</span>
          <strong className="power-budget-val">{totalAllocated} Units</strong>
        </div>
        <div className="power-budget-item">
          <span className="power-budget-label">Reserve Unallocated</span>
          <strong className="power-budget-val green">{unallocated} Units</strong>
        </div>
        <div className="power-budget-item">
          <span className="power-budget-label">Solar Panel Output</span>
          <strong className="power-budget-val">{Math.round(solarEfficiency * 100)}% Eff.</strong>
        </div>
      </div>

      {conservationDays > 0 && (
        <div className="power-conservation-notice">
          <Zap size={15} />
          <span>
            Emergency Conservation Active ({conservationDays}d left): Non-essential electricity draw
            is halved and Research is paused.
          </span>
        </div>
      )}

      <div className="power-sliders-list">
        {POWER_SYSTEMS.map((sys) => {
          const Icon = sys.icon
          const val = Math.round(draft[sys.key])
          const isLow = val < sys.minRecommended
          return (
            <div
              key={sys.key}
              className="power-slider-row"
              style={{ '--p-accent': sys.accent }}
            >
              <div className="power-slider-top">
                <div className="power-sys-label-group">
                  <span className="power-sys-icon">
                    <Icon size={16} />
                  </span>
                  <div>
                    <span className="power-sys-title">{sys.label}</span>
                    <span className="power-sys-priority">{sys.priority}</span>
                  </div>
                </div>

                <span className="power-sys-readout">
                  <strong>{val}</strong> <small>SIM UNITS</small>
                </span>
              </div>

              <input
                type="range"
                min={0}
                max={Math.max(maxBudget, val)}
                step={1}
                value={val}
                disabled={disabled || isSaving}
                onChange={(e) => handleSliderChange(sys.key, e.target.value)}
                aria-label={`${sys.label} electricity allocation`}
                className="power-range-input"
              />

              {isLow && (
                <div className="power-low-hint">
                  <AlertCircle size={13} />
                  <span>{sys.lowWarning}</span>
                </div>
              )}
            </div>
          )
        })}
      </div>

      <div className="power-panel-footer">
        <p className="power-priority-rule">
          Priority Rule: If battery power drops too low, lower-priority modules (Research, Comms,
          Greenhouse) automatically reduce power first so <strong>Life Support</strong> stays online!
        </p>

        <button
          type="submit"
          className="btn-apply-power"
          disabled={disabled || isSaving || !hasChanges}
        >
          <Zap size={16} />
          <span>{isSaving ? 'Updating Grid...' : hasChanges ? 'Apply Power Allocation' : 'Power Grid Synced'}</span>
        </button>
      </div>
    </form>
  )
}
