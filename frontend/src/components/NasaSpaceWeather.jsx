import { useEffect, useState } from 'react'
import { ExternalLink, Loader2, RefreshCw, Satellite } from 'lucide-react'
import { extractApiError, fetchNasaDashboardApi } from '../services/gameApi.js'
import './NasaSpaceWeather.css'

const EVENT_TABS = [
  { id: 'FLR', label: 'Solar Flares' },
  { id: 'SEP', label: 'Solar Energetic Particles' },
]

function formatEventTime(value) {
  if (!value) return 'Date not provided by NASA'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

function eventTitle(event) {
  if (event.event_type === 'SEP') return 'Solar Energetic Particle event'
  return event.class_type ? `Solar flare (${event.class_type})` : 'Solar flare'
}

function eventIdentifier(event) {
  return event.event_id || 'Not provided by NASA'
}

export default function NasaSpaceWeather() {
  const [weather, setWeather] = useState(null)
  const [activeTab, setActiveTab] = useState('FLR')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let active = true
    fetchNasaDashboardApi()
      .then((data) => {
        if (active) setWeather(data)
      })
      .catch((requestError) => {
        if (active) setError(extractApiError(requestError, 'NASA space-weather data could not be loaded.'))
      })
      .finally(() => {
        if (active) setIsLoading(false)
      })
    return () => {
      active = false
    }
  }, [])

  const refresh = async () => {
    setIsLoading(true)
    setError('')
    try {
      setWeather(await fetchNasaDashboardApi(true))
    } catch (requestError) {
      setError(extractApiError(requestError, 'NASA space-weather data could not be refreshed.'))
    } finally {
      setIsLoading(false)
    }
  }

  const connectionStatus = weather?.connection_status || 'unavailable'
  const events = weather?.events_by_type?.[activeTab] || []
  const eventError = weather?.event_errors?.[activeTab]
  const selectedTab = EVENT_TABS.find((tab) => tab.id === activeTab)
  const isUnavailable = connectionStatus === 'unavailable'

  return (
    <section className="mc-panel nasa-weather-panel" aria-labelledby="nasa-weather-heading">
      <div className="mc-panel-header">
        <div>
          <span className="mc-kicker">NASA DONKI // Real observations</span>
          <h2 id="nasa-weather-heading" className="mc-panel-title">
            NASA Space Weather Monitor
          </h2>
        </div>
        <button
          type="button"
          className="nasa-weather-refresh"
          onClick={refresh}
          disabled={isLoading}
        >
          {isLoading ? <Loader2 size={16} className="mc-spin-icon" /> : <RefreshCw size={16} />}
          {isLoading ? 'Loading NASA data...' : 'Refresh'}
        </button>
      </div>

      <div className={`nasa-weather-status ${isUnavailable ? 'unavailable' : connectionStatus}`}>
        <Satellite size={19} aria-hidden="true" />
        <strong>
          {isLoading && !weather
            ? 'CONNECTING TO NASA DONKI...'
            : connectionStatus === 'active'
            ? 'NASA SPACE WEATHER CONNECTION ACTIVE'
            : connectionStatus === 'partial'
            ? 'NASA DATA PARTIALLY AVAILABLE'
            : 'NASA DATA TEMPORARILY UNAVAILABLE'}
        </strong>
      </div>

      {error && (
        <p className="nasa-weather-error" role="alert">
          {error}
        </p>
      )}

      <div className="nasa-weather-stats">
        <div>
          <span>Last successful update</span>
          <strong>
            {weather?.retrieval_timestamp
              ? formatEventTime(weather.retrieval_timestamp)
              : 'Not available yet'}
          </strong>
        </div>
        <div>
          <span>{selectedTab?.label} in the last seven days</span>
          <strong>{events.length}</strong>
        </div>
      </div>

      <div className="nasa-weather-learning">
        <article>
          <h3>What are Solar Energetic Particles?</h3>
          <p>
            Particles from the Sun can travel through space at very high speeds. Some of these
            particles can create radiation hazards for astronauts.
          </p>
        </article>
        <article>
          <h3>Why do astronauts need shelters?</h3>
          <p>
            Protected areas can help astronauts reduce their exposure during dangerous
            space-weather events. DONKI records do not measure radiation dose at our lunar outpost.
          </p>
        </article>
      </div>

      <div className="nasa-weather-tabs" role="tablist" aria-label="NASA solar event type">
        {EVENT_TABS.map((tab) => (
          <button
            key={tab.id}
            id={`nasa-tab-${tab.id}`}
            type="button"
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-controls="nasa-event-panel"
            className={`nasa-weather-tab${activeTab === tab.id ? ' active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
            <span>{weather?.events_by_type?.[tab.id]?.length ?? 0}</span>
          </button>
        ))}
      </div>

      <div
        id="nasa-event-panel"
        className="nasa-weather-events"
        role="tabpanel"
        aria-labelledby={`nasa-tab-${activeTab}`}
      >
        <div className="nasa-weather-events-heading">
          <h3>{selectedTab?.label}</h3>
          <span className="nasa-real-data-label">REAL NASA DATA</span>
        </div>
        {isLoading && !weather ? (
          <p className="nasa-weather-empty">
            <Loader2 size={16} className="mc-spin-icon" /> Loading NASA event records...
          </p>
        ) : eventError ? (
          <p className="nasa-weather-error" role="status">{eventError}</p>
        ) : isUnavailable ? (
          <p className="nasa-weather-empty">
            NASA data is temporarily unavailable. The mission simulation is still playable.
          </p>
        ) : events.length === 0 ? (
          <p className="nasa-weather-empty">No relevant events found for the selected period.</p>
        ) : (
          <ul className="nasa-weather-event-list">
            {events.slice(0, 10).map((event) => (
              <li key={`${event.event_type}-${event.deduplication_key}`}>
                <div className="nasa-weather-event-top">
                  <strong>{eventTitle(event)}</strong>
                  {event.class_type && <span>Flare class: {event.class_type}</span>}
                </div>
                <dl className="nasa-weather-event-metadata">
                  <div>
                    <dt>Event date</dt>
                    <dd>
                      <time dateTime={event.event_time || undefined}>
                        {formatEventTime(event.event_time)}
                      </time>
                    </dd>
                  </div>
                  <div>
                    <dt>Event ID</dt>
                    <dd>{eventIdentifier(event)}</dd>
                  </div>
                  <div>
                    <dt>Category</dt>
                    <dd>{event.category || 'Not classified'}</dd>
                  </div>
                  {event.instruments?.length > 0 && (
                    <div>
                      <dt>Instruments</dt>
                      <dd>
                        {event.instruments
                          .map((instrument) => instrument.displayName)
                          .filter(Boolean)
                          .join(', ') || 'Details in NASA record'}
                      </dd>
                    </div>
                  )}
                  {event.retrieved_at && (
                    <div>
                      <dt>Retrieved</dt>
                      <dd>{formatEventTime(event.retrieved_at)}</dd>
                    </div>
                  )}
                </dl>
                {event.description && <p>{event.description}</p>}
                <p>{event.classification_explanation}</p>
                {event.source_url && (
                  <a href={event.source_url} target="_blank" rel="noopener noreferrer">
                    View NASA event record <ExternalLink size={14} />
                  </a>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>

      <p className="nasa-weather-notice">
        <strong>REAL NASA DATA</strong> shows observations from DONKI. Game resources and shelter
        effects are <strong>SIMULATED GAME CONSEQUENCES</strong>, not measured astronaut doses.
      </p>
    </section>
  )
}
