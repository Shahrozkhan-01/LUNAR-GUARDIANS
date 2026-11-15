import { CheckCircle2, AlertTriangle, ExternalLink } from 'lucide-react'
import './EventFeed.css'

export default function EventFeed({
  activeEvents = [],
  subsystems,
  crewHealth = 'Healthy',
  disabled = false,
  pendingAction = false,
  onResolveEvent,
  showOperationalStatus = true,
  emptyMessage = null,
}) {
  const statusItems = [
    {
      id: 'st-ls',
      title: subsystems?.oxygen_recycling_active
        ? 'Life support & oxygen recycling operational.'
        : 'Oxygen recycling offline — Life support running on base mode.',
      ok: Boolean(subsystems?.oxygen_recycling_active),
    },
    {
      id: 'st-solar',
      title: `Solar power generation at ${Math.round((subsystems?.solar_efficiency || 1) * 100)}% array efficiency.`,
      ok: (subsystems?.solar_efficiency || 1) >= 0.9,
    },
    {
      id: 'st-gh',
      title: subsystems?.greenhouse_active
        ? `Greenhouse active (${subsystems?.greenhouse_growth_days || 0}/2 growth days toward food harvest).`
        : 'Greenhouse crops paused.',
      ok: Boolean(subsystems?.greenhouse_active),
    },
    {
      id: 'st-crew',
      title: `Crew health monitoring active (${crewHealth}).`,
      ok: crewHealth === 'Healthy',
    },
  ]

  return (
    <div className="event-feed-box">
      {/* Active mission events with interactive player decisions */}
      {activeEvents.length === 0 && emptyMessage && (
        <p className="nasa-alert-empty">{emptyMessage}</p>
      )}
      {activeEvents.length > 0 && (
        <div className="active-events-stack">
          {activeEvents.map((ev) => (
            <article
              key={ev.event_id}
              className={`sim-event-card severity-${ev.severity}${ev.source_type === 'NASA' ? ' nasa-sim-event-card' : ''}`}
            >
              <div className="sim-event-header">
                <span className="sim-event-badge">
                  <AlertTriangle size={13} />
                  {ev.label}
                </span>
                {ev.source_type === 'NASA' ? (
                  <span className="nasa-event-category">
                    {ev.event_category || 'Educational awareness scenario'}
                  </span>
                ) : (
                  <span className={`sim-severity-pill ${ev.severity}`}>
                    Severity: {ev.severity.toUpperCase()}
                  </span>
                )}
              </div>

              <h3 className="sim-event-name">{ev.name}</h3>
              <p className="sim-event-desc">{ev.description}</p>
              {ev.source_type === 'NASA' && (
                <>
                  <dl className="nasa-event-details">
                    <div>
                      <dt>NASA event type</dt>
                      <dd>{ev.source_event_type === 'SEP' ? 'Solar Energetic Particles (SEP)' : 'Solar Flare (FLR)'}</dd>
                    </div>
                    <div>
                      <dt>NASA event date</dt>
                      <dd>{ev.source_event_time || 'Not provided by NASA'}</dd>
                    </div>
                    <div>
                      <dt>NASA event ID</dt>
                      <dd>{ev.source_event_id || 'Not provided by NASA'}</dd>
                    </div>
                  </dl>
                  {ev.educational_explanation && (
                    <p className="nasa-event-explanation">{ev.educational_explanation}</p>
                  )}
                  {ev.mission_situation && (
                    <p className="nasa-event-situation">{ev.mission_situation}</p>
                  )}
                  <div className="nasa-event-separation">
                    <span>REAL NASA DATA</span>
                    <span>{ev.consequence_label || 'SIMULATED GAME CONSEQUENCE'}</span>
                    {ev.source_url && (
                      <a href={ev.source_url} target="_blank" rel="noopener noreferrer">
                        NASA event record <ExternalLink size={13} />
                      </a>
                    )}
                  </div>
                </>
              )}

              <div className="sim-event-decisions">
                {ev.decisions.map((choice) => (
                  <button
                    key={choice.choice_id}
                    type="button"
                    className="sim-decision-btn"
                    disabled={disabled || pendingAction}
                    onClick={() => onResolveEvent(ev.event_id, choice.choice_id)}
                  >
                    <div className="sim-decision-top">
                      <strong>{choice.label}</strong>
                      <span className="sim-decision-cost">{choice.cost_text}</span>
                    </div>
                    <span className="sim-decision-consequence">{choice.consequence_text}</span>
                  </button>
                ))}
              </div>
            </article>
          ))}
        </div>
      )}

      {/* Outpost Operational Status Feed */}
      {showOperationalStatus && (
        <div className="event-feed-list">
          {statusItems.map((item) => (
            <div key={item.id} className="event-feed-item">
              <div className={`event-feed-check${item.ok ? '' : ' warn'}`} aria-hidden="true">
                <CheckCircle2 size={17} />
              </div>
              <div className="event-feed-content">
                <div className="event-feed-top">
                  <span className="event-feed-item-title">{item.title}</span>
                  <span className="event-feed-tag">SIMULATED</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
