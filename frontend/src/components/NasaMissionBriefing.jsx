import { useEffect, useState } from 'react'
import {
  Activity,
  AlertTriangle,
  Loader2,
  Mountain,
  Radio,
  RefreshCw,
  Satellite,
  Thermometer,
} from 'lucide-react'
import {
  extractApiError,
  fetchDatasetMetadataApi,
  fetchDatasetRecordsApi,
  fetchDatasetSummaryApi,
  fetchDatasetsApi,
} from '../services/gameApi.js'
import { MISSION_BRIEFING_PRESETS } from './nasaMissionBriefingConfig.js'
import './NasaMissionBriefing.css'

const DATASET_INFO = {
  diviner: {
    title: 'LUNAR ENVIRONMENT — DIVINER',
    icon: Thermometer,
    category: 'lunar_environment',
    purpose: 'Surface temperature affects thermal design, equipment operation, and energy planning.',
  },
  lola: {
    title: 'LUNAR TERRAIN — LOLA',
    icon: Mountain,
    category: 'lunar_terrain',
    purpose: 'Regional elevation context can inform broad mission planning and terrain discussions.',
  },
  ace_epam: {
    title: 'SPACE WEATHER — ACE EPAM',
    icon: Activity,
    category: 'space_weather',
    purpose: 'Energetic-particle measurements help teach why spacecraft monitor changing particle environments.',
  },
  stereo_impact: {
    title: 'SPACE WEATHER — STEREO-A',
    icon: Satellite,
    category: 'space_weather',
    purpose: 'Separate electron and proton channels illustrate how particle instruments report observations.',
  },
  jpl_horizons: {
    title: 'COMMUNICATION DELAY — JPL HORIZONS',
    icon: Radio,
    category: 'communication',
    purpose: 'Earth–Moon distance affects ideal light travel time and makes immediate conversation impossible.',
  },
}

const DATASET_IDS = Object.keys(DATASET_INFO)
const RECORD_DATASET_IDS = new Set(['ace_epam', 'stereo_impact', 'jpl_horizons'])

function displayNumber(value, digits = 4) {
  if (value === null || value === undefined || String(value).trim() === '') return 'Not available'
  const number = Number(value)
  return Number.isFinite(number)
    ? new Intl.NumberFormat(undefined, { maximumFractionDigits: digits }).format(number)
    : 'Not available'
}

function displayTimestamp(value) {
  if (!value) return 'Not available'
  const timestamp = String(value)
  return /(?:Z|UTC|[+-]\d{2}:\d{2})$/i.test(timestamp) ? timestamp : `${timestamp} UTC`
}

function StateMetric({ label, value, unit, derived = false }) {
  return (
    <div className="nasa-briefing-metric">
      <span>{label}</span>
      <strong>{value ?? 'Not available'}{unit ? <small> {unit}</small> : null}</strong>
      {derived && <em>DERIVED VALUE</em>}
    </div>
  )
}

function aceSample(summary, records, metadata) {
  const coverage = summary?.summary?.available_channel_coverage || {}
  const variables = Object.keys(coverage)
    .filter((name) => !name.startsWith('unc_') && coverage[name]?.valid_records > 0)
  for (const record of records || []) {
    for (const name of variables) {
      const measurement = record.measurements?.[name]
      if (measurement?.valid && measurement.value !== null) {
        return {
          timestamp: record.timestamp_utc,
          channel: name,
          value: displayNumber(measurement.value, 6),
          unit: metadata?.processing_metadata?.variables?.[name]?.units || '',
        }
      }
    }
  }
  return null
}

function loadDataset(datasetId, catalog) {
  const requests = [
    fetchDatasetMetadataApi(datasetId),
    fetchDatasetSummaryApi(datasetId),
  ]
  if (RECORD_DATASET_IDS.has(datasetId)) {
    requests.push(fetchDatasetRecordsApi(datasetId, 1, 20))
  }

  return Promise.allSettled(requests).then((results) => ({
    catalog,
    metadata: results[0].status === 'fulfilled' ? results[0].value : null,
    metadataError: results[0].status === 'rejected'
      ? extractApiError(results[0].reason, 'Dataset metadata is unavailable.')
      : '',
    summary: results[1].status === 'fulfilled' ? results[1].value : null,
    summaryError: results[1].status === 'rejected'
      ? extractApiError(results[1].reason, 'Dataset summary is unavailable.')
      : '',
    records: results[2]?.status === 'fulfilled' ? results[2].value.records || [] : [],
    recordsError: results[2]?.status === 'rejected'
      ? extractApiError(results[2].reason, 'Dataset records are unavailable.')
      : '',
  }))
}

function DatasetFacts({ datasetId, data, loading }) {
  const info = DATASET_INFO[datasetId]
  const Icon = info.icon
  const catalog = data?.catalog
  const summary = data?.summary?.summary
  const metadata = data?.metadata
  const coverage = data?.summary?.coverage || catalog?.coverage || metadata?.coverage
  const units = catalog?.units || metadata?.units
  const missing = !loading && (!data || (!metadata && !data.summary))
  const unavailable = !loading && (
    catalog?.availability?.status === 'unavailable'
    || metadata?.availability?.status === 'unavailable'
  )

  let measurements = null
  if (datasetId === 'diviner' && summary) {
    const channel = summary.columns?.tbol || summary.columns?.t9
    measurements = channel && (
      <>
        <StateMetric label="Tbol mean brightness temperature" value={displayNumber(channel.mean)} unit="K" derived />
        <StateMetric label="Valid / missing samples" value={`${channel.valid_count ?? 'Not available'} / ${channel.unknown_missing_count ?? 'Not available'}`} />
        <StateMetric label="Channel median" value={displayNumber(channel.median)} unit="K" derived />
      </>
    )
  } else if (datasetId === 'lola' && summary) {
    const stats = summary.height_m_relative_to_reference_radius_statistics || {}
    measurements = (
      <>
        <StateMetric label="Mean relative height" value={displayNumber(stats.height_m_mean)} unit="m" derived />
        <StateMetric label="Global height range" value={`${displayNumber(stats.height_m_minimum, 1)} to ${displayNumber(stats.height_m_maximum, 1)}`} unit="m" derived />
        <StateMetric label="Grid samples" value={stats.sample_count?.toLocaleString() || 'Not available'} />
      </>
    )
  } else if (datasetId === 'ace_epam' && summary) {
    const sample = aceSample(data.summary, data.records, metadata)
    measurements = (
      <>
        <StateMetric label="Archived measurement channels" value={summary.measurement_variable_count ?? 'Not available'} />
        <StateMetric label="Uncertainty channels" value={summary.uncertainty_variable_count ?? 'Not available'} />
        <StateMetric
          label={sample ? `Sample ${sample.channel} · ${displayTimestamp(sample.timestamp)}` : 'Representative valid sample'}
          value={sample?.value || 'No valid sample in loaded record page'}
          unit={sample?.unit || units}
        />
      </>
    )
  } else if (datasetId === 'stereo_impact' && summary) {
    const channel = metadata?.processing_metadata?.channels?.[0]
    const record = data.records?.[0]
    measurements = (
      <>
        <StateMetric label="Daily intervals" value={summary.record_count ?? 'Not available'} />
        <StateMetric label="Electron / proton channels" value={`${summary.electron_channel_count ?? '—'} / ${summary.proton_channel_count ?? '—'}`} />
        <StateMetric
          label={channel && record ? `${channel.particle} ${channel.energy_min_MeV}–${channel.energy_max_MeV} MeV · ${displayTimestamp(record.record_start_utc)}` : 'Sample measurement'}
          value={channel && record ? record[channel.intensity_field] : 'No sample available'}
          unit={channel?.intensity_units || units}
        />
        {channel && record && (
          <StateMetric
            label="Corresponding 1-sigma uncertainty"
            value={record[channel.uncertainty_field]}
            unit={channel.uncertainty_units}
          />
        )}
      </>
    )
  } else if (datasetId === 'jpl_horizons' && summary) {
    const range = summary.earth_moon_range_km || {}
    const oneWay = summary.one_way_down_leg_light_time_minutes || {}
    const twoWay = summary.two_way_vacuum_light_time_seconds_derived || {}
    const record = data.records?.[0]
    measurements = (
      <>
        <StateMetric label="Mean Earth–Moon range" value={displayNumber(range.mean, 3)} unit="km" />
        <StateMetric label="Mean one-way down-leg light time" value={displayNumber(oneWay.mean, 8)} unit="min" />
        <StateMetric label="Mean two-way vacuum light time" value={displayNumber(twoWay.mean, 8)} unit="s" derived />
        {record && (
          <p className="nasa-briefing-record-note">
            Sample epoch {displayTimestamp(record.epoch_utc)}: range {record.earth_moon_range_km} km;
            one-way {record.one_way_down_leg_light_time_minutes} min; derived two-way
            {' '}{record.two_way_vacuum_light_time_seconds_derived} s.
          </p>
        )}
      </>
    )
  }

  return (
    <article className={`nasa-briefing-dataset${missing || unavailable ? ' unavailable' : ''}`}>
      <div className="nasa-briefing-dataset-heading">
        <Icon size={20} aria-hidden="true" />
        <div>
          <h3>{info.title}</h3>
          <span>{catalog?.dataset_name || metadata?.dataset_name || 'NASA processed dataset'}</span>
        </div>
        <span className={`nasa-briefing-status ${loading ? '' : missing || unavailable ? 'offline' : datasetId === 'jpl_horizons' ? 'computed' : 'online'}`}>
          {loading ? 'LOADING' : missing || unavailable ? 'UNAVAILABLE' : datasetId === 'jpl_horizons' ? 'COMPUTED EPHEMERIS' : 'REAL NASA DATA'}
        </span>
      </div>

      {loading ? (
        <p className="nasa-briefing-unavailable" role="status">Loading dataset information…</p>
      ) : missing || unavailable ? (
        <p className="nasa-briefing-unavailable" role="status">
          {data?.metadataError || data?.summaryError || 'Dataset files are unavailable. No replacement measurements are shown.'}
        </p>
      ) : (
        <>
          <p className="nasa-briefing-purpose">{info.purpose}</p>
          <dl className="nasa-briefing-facts">
            <div><dt>Data coverage</dt><dd>{coverage || 'Not provided by the dataset API'}</dd></div>
            <div><dt>Units</dt><dd>{units || 'See channel-level unit labels below'}</dd></div>
            {datasetId === 'ace_epam' && summary?.time_coverage_utc && (
              <div><dt>Measurement period (UTC)</dt><dd>{summary.time_coverage_utc.start} – {summary.time_coverage_utc.end}</dd></div>
            )}
          </dl>
          <div className="nasa-briefing-metrics">{measurements || (
            <p className="nasa-briefing-unavailable">{data?.summaryError || 'No summary measurements are available.'}</p>
          )}</div>
          {datasetId === 'jpl_horizons' && summary?.future_ephemeris_epoch_count_at_retrieval > 0 && (
            <p className="nasa-briefing-record-note">
              {summary.future_ephemeris_epoch_count_at_retrieval} epochs were forward calculations at retrieval, not observations.
            </p>
          )}
          {datasetId === 'ace_epam' && data.recordsError && (
            <p className="nasa-briefing-record-note">Record sample unavailable: {data.recordsError}</p>
          )}
          {datasetId === 'stereo_impact' && data.recordsError && (
            <p className="nasa-briefing-record-note">Record sample unavailable: {data.recordsError}</p>
          )}
          {(catalog?.scientific_limitations || metadata?.scientific_limitations || []).length > 0 && (
            <ul className="nasa-briefing-limitations">
              {(catalog?.scientific_limitations || metadata?.scientific_limitations || []).map((limitation) => <li key={limitation}>{limitation}</li>)}
            </ul>
          )}
        </>
      )}
    </article>
  )
}

export default function NasaMissionBriefing({ selectedPreset, onSelectPreset }) {
  const [datasets, setDatasets] = useState({})
  const [catalogError, setCatalogError] = useState('')
  const [loading, setLoading] = useState(true)
  const [reloadKey, setReloadKey] = useState(0)
  const selected = MISSION_BRIEFING_PRESETS.find((preset) => preset.id === selectedPreset)
    || MISSION_BRIEFING_PRESETS[0]

  useEffect(() => {
    let active = true

    fetchDatasetsApi()
      .then(async (response) => {
        if (!active) return
        const catalogById = Object.fromEntries(
          (response.datasets || []).map((dataset) => [dataset.dataset_id, dataset]),
        )
        const results = await Promise.all(
          DATASET_IDS.map((datasetId) => loadDataset(datasetId, catalogById[datasetId])),
        )
        if (active) {
          setDatasets(Object.fromEntries(DATASET_IDS.map((datasetId, index) => [datasetId, results[index]])))
        }
      })
      .catch((error) => {
        if (active) {
          setDatasets({})
          setCatalogError(extractApiError(error, 'NASA dataset catalog is unavailable.'))
        }
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => { active = false }
  }, [reloadKey])

  return (
    <section className="setup-block nasa-mission-briefing" aria-labelledby="nasa-mission-briefing-title">
      <div className="setup-block-header">
        <span className="setup-step-num">NASA MISSION BRIEFING</span>
        <h2 id="nasa-mission-briefing-title" className="setup-block-title">Explore the science before launch</h2>
        <p className="nasa-briefing-intro">
          Review archived observations and computed ephemerides as educational context. These data do not set or change game resources.
        </p>
      </div>

      <div className="nasa-briefing-presets" role="group" aria-label="Select an educational mission briefing">
        {MISSION_BRIEFING_PRESETS.map((preset) => (
          <button
            key={preset.id}
            type="button"
            aria-pressed={selected.id === preset.id}
            className={`nasa-briefing-preset${selected.id === preset.id ? ' selected' : ''}`}
            onClick={() => onSelectPreset(preset.id)}
          >
            <span>{preset.title}</span>
            <small>{preset.objective}</small>
          </button>
        ))}
      </div>

      <article className="nasa-briefing-scenario">
        <div>
          <span className="nasa-briefing-kicker">SELECTED TRAINING SCENARIO</span>
          <h3>{selected.title}</h3>
          <p><strong>Objective:</strong> {selected.objective}</p>
          <p><strong>Scientific background:</strong> {selected.background}</p>
          <p><strong>Planning challenge:</strong> {selected.challenge}</p>
        </div>
        <div className="nasa-briefing-scenario-facts">
          <div>
            <strong>Relevant NASA datasets</strong>
            <span>{selected.datasets.map((id) => DATASET_INFO[id].title.replace(' — ', ': ')).join(' · ')}</span>
          </div>
          <ul>{selected.limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}</ul>
        </div>
      </article>

      <div className="nasa-briefing-labels" aria-label="Data interpretation labels">
        <span className="nasa-briefing-status online">REAL NASA DATA</span>
        <span className="nasa-briefing-status computed">COMPUTED EPHEMERIS</span>
        <span className="nasa-briefing-status derived">DERIVED VALUE</span>
        <span className="nasa-briefing-status simulated">SIMULATED GAME CONSEQUENCE</span>
      </div>

      {catalogError && (
        <div className="nasa-briefing-alert" role="alert">
          <AlertTriangle size={18} />
          <div><strong>NASA dataset service unavailable</strong><p>{catalogError} Mission setup and launch remain available.</p></div>
          <button type="button" onClick={() => {
            setLoading(true)
            setCatalogError('')
            setReloadKey((key) => key + 1)
          }}>
            <RefreshCw size={15} /> Retry
          </button>
        </div>
      )}

      {loading && (
        <div className="nasa-briefing-loading" role="status">
          <Loader2 size={18} className="nasa-briefing-spin" /> Loading NASA briefing data…
        </div>
      )}

      <div className="nasa-briefing-datasets">
        {DATASET_IDS.map((datasetId) => (
          <DatasetFacts key={datasetId} datasetId={datasetId} data={datasets[datasetId]} loading={loading} />
        ))}
      </div>

      <p className="nasa-briefing-date-note">
        Historical ACE and STEREO-A samples come from different archived dates and are not presented as one simultaneous space-weather event.
        NASA observations and computed values are briefing context only; any later game outcomes remain simulated.
      </p>
    </section>
  )
}
