import { CheckCircle2, ExternalLink, Radio, Shield, Sparkles } from 'lucide-react'
import './NasaTrainingEvents.css'

const DATA_LABELS = {
  'REAL NASA DATA': 'nasa',
  'COMPUTED EPHEMERIS': 'computed',
  'DERIVED VALUE': 'derived',
}

const CHANGE_LABELS = {
  power: 'Power',
  water: 'Water',
  oxygen: 'Oxygen',
  food: 'Food',
  shield: 'Shield protection',
  radiation_exposure: 'Radiation indicator',
  science_points: 'Science points',
  'power_allocation.radiation_shelter': 'Shelter power allocation',
  'power_allocation.scientific_research': 'Research power allocation',
}

function isAffordable(decision, resources) {
  return Object.entries(decision.required_resources || {}).every(
    ([resource, required]) => (resources?.[resource] ?? 0) >= required
  )
}

function formatChange(value) {
  return `${value > 0 ? '+' : ''}${value}`
}

function TrainingData({ points }) {
  if (!points?.length) return null

  return (
    <div className="nasa-training-data">
      {points.map((point, index) => (
        <article className="nasa-training-data-point" key={`${point.dataset_id}-${index}`}>
          <div className="nasa-training-data-heading">
            <span className={`nasa-data-label ${DATA_LABELS[point.data_label] || ''}`}>
              {point.data_label}
            </span>
            <strong>{point.dataset_name}</strong>
          </div>
          <p className="nasa-training-measurement">{point.measurement}</p>
          <p className="nasa-training-value">
            {point.value}
            {point.unit ? <span> {point.unit}</span> : null}
          </p>
          {point.date_or_coverage && (
            <p className="nasa-training-date">
              Date / coverage: {point.date_or_coverage}
            </p>
          )}
          {point.note && <p className="nasa-training-note">{point.note}</p>}
          <p className="nasa-training-source">
            Source: {point.source}
            {point.source_url && (
              <a href={point.source_url} target="_blank" rel="noopener noreferrer">
                Open source <ExternalLink size={12} />
              </a>
            )}
          </p>
        </article>
      ))}
    </div>
  )
}

function DecisionResult({ event }) {
  if (!event.resolved) return null

  return (
    <div className="nasa-training-result" aria-live="polite">
      <div className="nasa-training-result-title">
        <CheckCircle2 size={17} />
        <strong>{event.consequence_label}</strong>
      </div>
      <p>{event.result_message}</p>
      {event.decision_rationale && <p>{event.decision_rationale}</p>}
      {Object.keys(event.resource_changes || {}).length > 0 && (
        <ul>
          {Object.entries(event.resource_changes).map(([key, value]) => (
            <li key={key}>
              {CHANGE_LABELS[key] || key}: {formatChange(value)}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default function NasaTrainingEvents({
  events = [],
  resources,
  disabled = false,
  pendingAction = false,
  onResolveEvent,
}) {
  if (!events.length) {
    return (
      <p className="nasa-training-empty">
        No training scenarios are available for this mission.
      </p>
    )
  }

  return (
    <div className="nasa-training-grid">
      {events.map((event) => (
        <article
          className={`nasa-training-card${event.resolved ? ' is-resolved' : ''}`}
          key={event.event_id}
        >
          <header className="nasa-training-card-header">
            <span className="nasa-training-event-label">
              <Sparkles size={13} />
              {event.label}
            </span>
            <span className={`nasa-training-availability ${event.data_availability}`}>
              NASA context {event.data_availability}
            </span>
          </header>

          <h3>{event.title}</h3>
          <p className="nasa-training-description">{event.description}</p>
          <p className="nasa-training-context">{event.scientific_context}</p>

          {event.data_unavailable_note && (
            <p className="nasa-training-unavailable" role="status">
              NASA dataset context unavailable. {event.data_unavailable_note}
            </p>
          )}
          <TrainingData points={event.data_context} />

          <div className="nasa-training-limitations">
            <strong>Scientific limitations</strong>
            <ul>
              {event.scientific_limitations.map((limitation) => (
                <li key={limitation}>{limitation}</li>
              ))}
            </ul>
          </div>

          {event.resolved ? (
            <DecisionResult event={event} />
          ) : (
            <div className="nasa-training-decisions">
              <h4>Choose a training response</h4>
              {event.decisions.map((decision) => {
                const affordable = isAffordable(decision, resources)
                return (
                  <button
                    className="nasa-training-decision"
                    key={decision.choice_id}
                    type="button"
                    disabled={disabled || pendingAction || !affordable}
                    title={!affordable ? 'Not enough simulated game resources' : undefined}
                    onClick={() => onResolveEvent(event.event_id, decision.choice_id)}
                  >
                    <span className="nasa-training-decision-title">
                      {event.category === 'space_weather_preparedness' ? (
                        <Shield size={15} />
                      ) : event.category === 'earth_moon_communication' ? (
                        <Radio size={15} />
                      ) : (
                        <Sparkles size={15} />
                      )}
                      <strong>{decision.label}</strong>
                    </span>
                    <span className="nasa-training-cost">{decision.cost_text}</span>
                    <span className="nasa-training-consequence">
                      {decision.consequence_text}
                    </span>
                    {decision.rationale && (
                      <span className="nasa-training-rationale">
                        Why it matters: {decision.rationale}
                      </span>
                    )}
                  </button>
                )
              })}
            </div>
          )}
        </article>
      ))}
    </div>
  )
}
