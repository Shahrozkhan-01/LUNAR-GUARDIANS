import { useEffect, useMemo, useState } from 'react'
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  Database,
  ExternalLink,
  Loader2,
  RefreshCw,
  Satellite,
} from 'lucide-react'
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import Navbar from '../components/Navbar.jsx'
import Footer from '../components/Footer.jsx'
import {
  extractApiError,
  fetchDatasetMetadataApi,
  fetchDatasetRecordsApi,
  fetchDatasetSummaryApi,
  fetchDatasetsApi,
} from '../services/gameApi.js'
import './NasaDataExplorer.css'

const PAGE_SIZE = 20
const CHART_COLOR = '#45d9f3'

function displayNumber(value, digits = 2) {
  if (value === null || value === undefined || String(value).trim() === '') return 'Missing'
  const number = Number(value)
  return Number.isFinite(number)
    ? new Intl.NumberFormat(undefined, { maximumFractionDigits: digits }).format(number)
    : 'Not available'
}

function numericValue(value) {
  if (value === null || value === undefined || String(value).trim() === '') return null
  const number = Number(value)
  return Number.isFinite(number) ? number : null
}

function datasetLabel(dataset) {
  if (dataset.data_type === 'computed_ephemeris') return 'COMPUTED EPHEMERIS'
  return 'REAL NASA DATA'
}

function toChartDate(value) {
  if (!value) return ''
  return `${String(value).slice(0, 16).replace('T', ' ')} UTC`
}

function SummaryStatistics({ datasetId, summary }) {
  if (!summary) return null

  if (datasetId === 'diviner') {
    const columns = Object.entries(summary.columns || {})
      .filter(([name, value]) => /^t(?:\d|bol)/.test(name) && value)
    return (
      <section className="nasa-explorer-panel nasa-explorer-summary" aria-label="Diviner summary statistics">
        <div className="nasa-explorer-panel-heading">
          <div><span className="nasa-explorer-eyebrow">BACKEND SUMMARY STATISTICS</span><h3>Brightness-temperature channels</h3></div>
          <span className="nasa-data-tag real">REAL NASA DATA</span>
        </div>
        <div className="nasa-explorer-table-wrap">
          <table className="nasa-explorer-table">
            <thead><tr><th>Channel</th><th>Valid samples</th><th>Missing</th><th>Minimum (K)</th><th>Median (K)</th><th>Mean (K)</th><th>Maximum (K)</th></tr></thead>
            <tbody>{columns.map(([name, value]) => (
              <tr key={name}>
                <td>{name.toUpperCase()}</td>
                <td>{value.valid_count ?? '—'}</td>
                <td>{value.unknown_missing_count ?? value.invalid_sentinel_count ?? '—'}</td>
                <td>{displayNumber(value.minimum, 4)}</td>
                <td>{displayNumber(value.median, 4)}</td>
                <td>{displayNumber(value.mean, 4)}</td>
                <td>{displayNumber(value.maximum, 4)}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </section>
    )
  }

  if (datasetId === 'lola') {
    const globalStats = summary.height_m_relative_to_reference_radius_statistics || {}
    const bands = Object.entries(summary.latitude_band_height_statistics || {})
    return (
      <section className="nasa-explorer-panel nasa-explorer-summary" aria-label="LOLA summary statistics">
        <div className="nasa-explorer-panel-heading">
          <div><span className="nasa-explorer-eyebrow">BACKEND SUMMARY STATISTICS</span><h3>Broad-scale elevation</h3></div>
          <span className="nasa-data-tag derived">DERIVED VALUE</span>
        </div>
        <p className="nasa-explorer-chart-range">
          Global relative height; summary values are derived from the preserved integer samples.
        </p>
        <div className="nasa-explorer-table-wrap">
          <table className="nasa-explorer-table">
            <thead><tr><th>Region</th><th>Samples</th><th>Minimum (m)</th><th>Median (m)</th><th>Mean (m)</th><th>Maximum (m)</th></tr></thead>
            <tbody>
              <tr>
                <td>Global</td><td>{globalStats.sample_count ?? '—'}</td>
                <td>{displayNumber(globalStats.height_m_minimum, 1)}</td>
                <td>{displayNumber(globalStats.height_m_median, 1)}</td>
                <td>{displayNumber(globalStats.height_m_mean, 1)}</td>
                <td>{displayNumber(globalStats.height_m_maximum, 1)}</td>
              </tr>
              {bands.map(([name, value]) => (
                <tr key={name}>
                  <td>{value.latitude_bounds_degrees ? `${value.latitude_bounds_degrees[0]}° to ${value.latitude_bounds_degrees[1]}°` : name}</td>
                  <td>{value.sample_count ?? '—'}</td>
                  <td>{displayNumber(value.height_m_minimum, 1)}</td>
                  <td>{displayNumber(value.height_m_median, 1)}</td>
                  <td>{displayNumber(value.height_m_mean, 1)}</td>
                  <td>{displayNumber(value.height_m_maximum, 1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {summary.extrema_warning && <p className="nasa-explorer-warning">{summary.extrema_warning}</p>}
      </section>
    )
  }
  if (datasetId === 'jpl_horizons') {
    const range = summary.earth_moon_range_km || {}
    const lightTime = summary.one_way_down_leg_light_time_minutes || {}
    return (
      <section className="nasa-explorer-panel nasa-explorer-summary" aria-label="Horizons summary statistics">
        <div className="nasa-explorer-panel-heading">
          <div><span className="nasa-explorer-eyebrow">BACKEND SUMMARY STATISTICS</span><h3>Computed ephemeris values</h3></div>
          <span className="nasa-data-tag computed">COMPUTED EPHEMERIS</span>
        </div>
        <div className="nasa-explorer-summary-cards">
          <div><span>Epochs</span><strong>{summary.epoch_count ?? '—'}</strong></div>
          <div><span>Range min / max (km)</span><strong>{displayNumber(range.minimum, 2)} / {displayNumber(range.maximum, 2)}</strong></div>
          <div><span>Mean range (km)</span><strong>{displayNumber(range.mean, 2)}</strong></div>
          <div><span>One-way light time mean (min)</span><strong>{displayNumber(lightTime.mean, 8)}</strong></div>
          <div><span>Future calculations at retrieval</span><strong>{summary.future_ephemeris_epoch_count_at_retrieval ?? '—'}</strong></div>
        </div>
      </section>
    )
  }

  if (datasetId === 'ace_epam') {
    return (
      <section className="nasa-explorer-summary-cards" aria-label="ACE EPAM summary statistics">
        <div><span>Archived records</span><strong>{summary.record_count ?? '—'}</strong></div>
        <div><span>Measurement channels</span><strong>{summary.measurement_variable_count ?? '—'}</strong></div>
        <div><span>Uncertainty channels</span><strong>{summary.uncertainty_variable_count ?? '—'}</strong></div>
        <div><span>Valid numeric values</span><strong>
          {summary.total_valid_numeric_values ?? '—'} / {summary.total_numeric_measurement_and_uncertainty_values ?? '—'}
        </strong></div>
      </section>
    )
  }

  if (datasetId === 'stereo_impact') {
    return (
      <section className="nasa-explorer-summary-cards" aria-label="STEREO-A summary statistics">
        <div><span>Daily intervals</span><strong>{summary.record_count ?? '—'}</strong></div>
        <div><span>Electron channels</span><strong>{summary.electron_channel_count ?? '—'}</strong></div>
        <div><span>Proton channels</span><strong>{summary.proton_channel_count ?? '—'}</strong></div>
        <div><span>Total channels</span><strong>{summary.channel_count ?? '—'}</strong></div>
      </section>
    )
  }

  if (datasetId === 'omni_hourly') {
    return (
      <section className="nasa-explorer-summary-cards" aria-label="OMNI summary statistics">
        <div><span>Hourly records</span><strong>{summary.record_count ?? '—'}</strong></div>
        <div><span>Interval</span><strong>Jan 2020</strong></div>
        <div><span>Fill values retained</span><strong>Yes</strong></div>
        <div><span>Source location</span><strong>Near-Earth / L1</strong></div>
      </section>
    )
  }



  if (datasetId === 'lend') {
    const coverage = summary.spatial_coverage || {}
    return (
      <section className="nasa-explorer-summary-cards" aria-label="LEND summary statistics">
        <div><span>Orbital records</span><strong>{summary.record_count ?? '—'}</strong></div>
        <div><span>Historical interval</span><strong>1 Jan 2020 UTC</strong></div>
        <div><span>Latitude range</span><strong>{displayNumber(coverage.latitude_min_deg, 1)}° to {displayNumber(coverage.latitude_max_deg, 1)}°</strong></div>
        <div><span>Neutron unit</span><strong>counts</strong></div>
      </section>
    )
  }

  if (datasetId === 'lro_spice') {
    const distance = summary.distance_from_moon_center_km || {}
    return (
      <section className="nasa-explorer-summary-cards" aria-label="LRO SPICE summary statistics">
        <div><span>Computed positions</span><strong>{summary.record_count ?? '—'}</strong></div>
        <div><span>Frame</span><strong>J2000</strong></div>
        <div><span>Distance min / max (km)</span><strong>{displayNumber(distance.minimum, 1)} / {displayNumber(distance.maximum, 1)}</strong></div>
        <div><span>Geometry type</span><strong>SPICE computed</strong></div>
      </section>
    )
  }

  if (datasetId === 'osd53') {
    return (
      <section className="nasa-explorer-summary-cards" aria-label="OSD-53 summary statistics">
        <div><span>Study samples</span><strong>{summary.sample_count ?? '—'}</strong></div>
        <div><span>Gene summaries</span><strong>{summary.gene_summary_count ?? '—'}</strong></div>
        <div><span>Pre-flight samples</span><strong>{summary.preflight_sample_count ?? '—'}</strong></div>
        <div><span>Post-flight samples</span><strong>{summary.postflight_sample_count ?? '—'}</strong></div>
      </section>
    )
  }

  return null
}

function SummaryChart({ dataset, summary, records, aceVariable, setAceVariable, stereoChannel, setStereoChannel, variableOptions, stereoChannels }) {
  let chartData = []
  let chartTitle = ''
  let unit = ''
  let chartType = 'summary'
  let secondSeries = null

  if (dataset.dataset_id === 'diviner') {
    chartTitle = 'Historical channel mean brightness temperature'
    unit = 'K'
    const columns = summary?.columns || {}
    chartData = Object.entries(columns)
      .filter(([name, value]) => /^t(?:\d|bol)/.test(name) && Number.isFinite(value?.mean))
      .map(([name, value]) => ({ date: name.toUpperCase(), value: value.mean }))
  } else if (dataset.dataset_id === 'lola') {
    chartTitle = 'Mean elevation by latitude band'
    unit = 'm relative to reference radius'
    const bands = summary?.latitude_band_height_statistics || {}
    chartData = Object.entries(bands)
      .filter(([, value]) => Number.isFinite(value?.height_m_mean))
      .map(([name, value]) => ({
        date: `${name.replace('_to_', '° to ')}°`,
        value: value.height_m_mean,
      }))
  } else if (dataset.dataset_id === 'jpl_horizons') {
    chartTitle = 'Computed Earth–Moon range by epoch'
    unit = 'km'
    chartType = 'records'
    chartData = (records || []).map((record) => ({
      date: toChartDate(record.epoch_utc),
      value: numericValue(record.earth_moon_range_km),
    })).filter((point) => point.value !== null)
  } else if (dataset.dataset_id === 'ace_epam') {
    chartTitle = `Historical ACE EPAM ${aceVariable} channel`
    unit = dataset.processing_metadata?.variables?.[aceVariable]?.units || 'See variable metadata'
    chartType = 'records'
    chartData = (records || []).map((record) => {
      const measurement = record.measurements?.[aceVariable]
      return {
        date: toChartDate(record.timestamp_utc),
        value: measurement?.valid ? measurement.value : null,
      }
    })
  } else if (dataset.dataset_id === 'stereo_impact') {
    const channel = stereoChannels.find((item) => item.name === stereoChannel) || stereoChannels[0]
    chartTitle = channel ? `Historical STEREO-A ${channel.particle} channel` : 'Historical STEREO-A channel'
    unit = channel?.intensity_units || 'See channel metadata'
    chartType = 'records'
    secondSeries = 'uncertainty'
    chartData = (records || []).map((record) => ({
      date: toChartDate(record.record_start_utc),
      value: numericValue(record[channel?.intensity_field]),
      uncertainty: numericValue(record[channel?.uncertainty_field]),
    }))
  } else if (dataset.dataset_id === 'omni_hourly') {
    chartTitle = 'Historical OMNI solar-wind speed'
    unit = 'km/s'
    chartType = 'records'
    chartData = (records || []).map((record) => ({
      date: toChartDate(record.timestamp_utc),
      value: numericValue(record.solar_wind_speed_km_s),
    }))
  } else if (dataset.dataset_id === 'lend') {
    chartTitle = 'Historical LEND corrected CSETN neutron counts'
    unit = 'counts'
    chartType = 'records'
    chartData = (records || []).map((record) => ({
      date: toChartDate(record.timestamp_utc),
      value: numericValue(record.csetn_sum_counts),
    }))
  } else if (dataset.dataset_id === 'lro_spice') {
    chartTitle = 'Historical LRO distance from Moon center'
    unit = 'km'
    chartType = 'records'
    chartData = (records || []).map((record) => ({
      date: toChartDate(record.timestamp_utc),
      value: numericValue(record.distance_from_moon_center_km),
    }))
  } else if (dataset.dataset_id === 'osd53') {
    chartTitle = 'OSD-53 sample counts by flight phase'
    unit = 'samples'
    chartData = [
      { date: 'Pre-flight', value: numericValue(summary?.preflight_sample_count) },
      { date: 'Post-flight', value: numericValue(summary?.postflight_sample_count) },
    ]
  }

  const hasData = chartData.some((point) => Number.isFinite(point.value))
  return (
    <section className="nasa-explorer-panel" aria-label="Dataset visualization">
      <div className="nasa-explorer-panel-heading">
        <div>
          <span className="nasa-explorer-eyebrow">DATA VISUALIZATION</span>
          <h3>{chartTitle}</h3>
          <p>Values are shown only where present in the selected dataset.</p>
          {dataset.dataset_id === 'lola' && <span className="nasa-data-tag derived">DERIVED VALUE</span>}
        </div>
        {dataset.dataset_id === 'ace_epam' && variableOptions.length > 0 && (
          <label className="nasa-explorer-select">
            <span>Measurement channel</span>
            <select value={aceVariable} onChange={(event) => setAceVariable(event.target.value)}>
              {variableOptions.map((option) => (
                <option key={option.name} value={option.name}>{option.name}</option>
              ))}
            </select>
          </label>
        )}
        {dataset.dataset_id === 'stereo_impact' && stereoChannels.length > 0 && (
          <label className="nasa-explorer-select">
            <span>Measurement channel</span>
            <select value={stereoChannel || stereoChannels[0].name} onChange={(event) => setStereoChannel(event.target.value)}>
              {stereoChannels.map((channel) => (
                <option key={channel.name} value={channel.name}>
                  {channel.particle}: {channel.energy_min_MeV}–{channel.energy_max_MeV} MeV
                </option>
              ))}
            </select>
          </label>
        )}
      </div>
      {chartType === 'records' && (
        <p className="nasa-explorer-chart-range">
          Showing loaded record page only. Missing channel values are left blank; no interpolation is applied.
        </p>
      )}
      {hasData ? (
        <div className="nasa-explorer-chart">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 10, right: 20, left: 4, bottom: 28 }}>
              <CartesianGrid stroke="rgba(170, 197, 230, 0.12)" strokeDasharray="4 5" />
              <XAxis
                dataKey="date"
                tick={{ fill: '#9eb3ce', fontSize: 10 }}
                angle={-24}
                textAnchor="end"
                interval="preserveStartEnd"
                height={54}
              />
              <YAxis
                tick={{ fill: '#9eb3ce', fontSize: 10 }}
                width={78}
                label={{ value: unit, angle: -90, position: 'insideLeft', fill: '#9eb3ce', fontSize: 10 }}
              />
              <Tooltip
                contentStyle={{ background: '#0b1026', border: '1px solid rgba(69, 217, 243, .35)', borderRadius: 10 }}
                labelStyle={{ color: '#fff' }}
                formatter={(value, name) => [displayNumber(value, 5), name === 'uncertainty' ? '1-sigma uncertainty' : unit]}
              />
              <Line
                type="linear"
                dataKey="value"
                name={unit}
                stroke={CHART_COLOR}
                strokeWidth={2}
                dot={{ r: dataset.dataset_id === 'diviner' || dataset.dataset_id === 'lola' ? 3 : 2 }}
                activeDot={{ r: 5 }}
                connectNulls={false}
                isAnimationActive={false}
              />
              {secondSeries && (
                <Line
                  type="linear"
                  dataKey="uncertainty"
                  name="uncertainty"
                  stroke="#ffb454"
                  strokeWidth={1.5}
                  dot={{ r: 2 }}
                  connectNulls={false}
                  isAnimationActive={false}
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div className="nasa-explorer-chart-empty">
          {chartType === 'records'
            ? 'No valid measurements are available on this record page.'
            : 'No summary values are available to chart.'}
        </div>
      )}
    </section>
  )
}

function RecordsTable({ dataset, records, pagination, loading, error, onPageChange, onRetry, aceVariable, stereoChannels, stereoChannel }) {
  if (!dataset.record_access?.available) return null
  const selectedStereo = stereoChannels.find((channel) => channel.name === stereoChannel) || stereoChannels[0]

  return (
    <section className="nasa-explorer-panel" aria-label="Dataset records">
      <div className="nasa-explorer-panel-heading">
        <div>
          <span className="nasa-explorer-eyebrow">PAGINATED SOURCE RECORDS</span>
          <h3>Measurements</h3>
          <p>{pagination?.total_records ?? '—'} records in this archived dataset</p>
        </div>
      </div>
      {error && (
        <div className="nasa-explorer-alert" role="alert">
          <AlertTriangle size={18} />
          <span>{error}</span>
          <button type="button" className="nasa-explorer-button" onClick={onRetry}>
            <RefreshCw size={15} /> Retry
          </button>
        </div>
      )}
      {loading ? (
        <div className="nasa-explorer-inline-state"><Loader2 className="nasa-explorer-spin" size={18} /> Loading records…</div>
      ) : records && pagination ? (
        <>
          <div className="nasa-explorer-table-wrap">
            <table className="nasa-explorer-table">
              <thead>
                {dataset.dataset_id === 'ace_epam' && (
                  <tr><th>UTC timestamp</th><th>{aceVariable}</th><th>Validity</th></tr>
                )}
                {dataset.dataset_id === 'stereo_impact' && (
                  <tr><th>Interval start (UTC)</th><th>Interval end (UTC)</th><th>Intensity</th><th>1-sigma uncertainty</th></tr>
                )}
                {dataset.dataset_id === 'jpl_horizons' && (
                  <tr><th>Epoch (UTC)</th><th>Range (km)</th><th>Range rate (km/s)</th><th>One-way light time (min)</th><th>Two-way vacuum light time (s, derived)</th></tr>
                )}
                {dataset.dataset_id === 'omni_hourly' && (
                  <tr><th>UTC timestamp</th><th>Solar-wind speed (km/s)</th><th>Proton density (cm⁻³)</th><th>IMF magnitude (nT)</th><th>Validity note</th></tr>
                )}
                {dataset.dataset_id === 'lend' && (
                  <tr><th>UTC timestamp</th><th>Latitude (°)</th><th>East longitude (°)</th><th>CSETN sum (counts)</th><th>1-sigma (counts)</th></tr>
                )}
                {dataset.dataset_id === 'lro_spice' && (
                  <tr><th>UTC timestamp</th><th>X (km, J2000)</th><th>Y (km, J2000)</th><th>Z (km, J2000)</th><th>Distance from Moon center (km)</th></tr>
                )}
                {dataset.dataset_id === 'osd53' && (
                  <tr><th>Sample ID</th><th>Organism</th><th>Material</th><th>Flight phase</th><th>Time</th></tr>
                )}
              </thead>
              <tbody>
                {records.length === 0 && (
                  <tr><td colSpan={dataset.dataset_id === 'jpl_horizons' ? 5 : dataset.dataset_id === 'stereo_impact' ? 4 : dataset.dataset_id === 'omni_hourly' || dataset.dataset_id === 'lend' || dataset.dataset_id === 'lro_spice' || dataset.dataset_id === 'osd53' ? 5 : 3}>
                    {pagination.total_records === 0 ? 'This dataset contains no records.' : 'No records on this page.'}
                  </td></tr>
                )}
                {records.map((record, index) => {
                  if (dataset.dataset_id === 'ace_epam') {
                    const measurement = record.measurements?.[aceVariable]
                    return (
                      <tr key={`${record.timestamp_utc}-${index}`}>
                        <td>{record.timestamp_utc}</td>
                        <td>{measurement?.valid ? displayNumber(measurement.value, 6) : 'Missing'}</td>
                        <td><span className={`nasa-explorer-validity ${measurement?.valid ? 'valid' : 'missing'}`}>{measurement?.valid ? 'Valid' : 'Missing / fill'}</span></td>
                      </tr>
                    )
                  }
                  if (dataset.dataset_id === 'omni_hourly') {
                    const hasFill = record.solar_wind_speed_km_s === '9999' || record.proton_density_cm3 === '999.9' || record.imf_magnitude_nt === '999.9'
                    return (
                      <tr key={`${record.timestamp_utc}-${index}`}>
                        <td>{record.timestamp_utc}</td>
                        <td>{record.solar_wind_speed_km_s === '9999' ? 'Missing' : displayNumber(record.solar_wind_speed_km_s, 1)}</td>
                        <td>{record.proton_density_cm3 === '999.9' ? 'Missing' : displayNumber(record.proton_density_cm3, 2)}</td>
                        <td>{record.imf_magnitude_nt === '999.9' ? 'Missing' : displayNumber(record.imf_magnitude_nt, 1)}</td>
                        <td>{hasFill ? 'Official fill value present' : 'Available'}</td>
                      </tr>
                    )
                  }
                  if (dataset.dataset_id === 'lend') {
                    return (
                      <tr key={`${record.timestamp_utc}-${index}`}>
                        <td>{record.timestamp_utc}</td>
                        <td>{displayNumber(record.lunarcentric_latitude_deg, 3)}</td>
                        <td>{displayNumber(record.lunarcentric_east_longitude_deg, 3)}</td>
                        <td>{displayNumber(record.csetn_sum_counts, 3)}</td>
                        <td>{displayNumber(record.csetn_sum_sigma_counts, 3)}</td>
                      </tr>
                    )
                  }
                  if (dataset.dataset_id === 'lro_spice') {
                    return (
                      <tr key={`${record.timestamp_utc}-${index}`}>
                        <td>{record.timestamp_utc}</td>
                        <td>{displayNumber(record.x_km, 2)}</td>
                        <td>{displayNumber(record.y_km, 2)}</td>
                        <td>{displayNumber(record.z_km, 2)}</td>
                        <td>{displayNumber(record.distance_from_moon_center_km, 2)}</td>
                      </tr>
                    )
                  }
                  if (dataset.dataset_id === 'osd53') {
                    return (
                      <tr key={`${record.sample_id}-${index}`}>
                        <td>{record.sample_id}</td>
                        <td>{record.organism}</td>
                        <td>{record.material_type}</td>
                        <td>{record.spaceflight}</td>
                        <td>{record.time}</td>
                      </tr>
                    )
                  }
                  if (dataset.dataset_id === 'stereo_impact') {
                    return (
                      <tr key={`${record.record_start_utc}-${index}`}>
                        <td>{record.record_start_utc}</td>
                        <td>{record.record_end_utc}</td>
                        <td>{displayNumber(record[selectedStereo?.intensity_field], 6)}</td>
                        <td>{displayNumber(record[selectedStereo?.uncertainty_field], 6)}</td>
                      </tr>
                    )
                  }
                  return (
                    <tr key={`${record.epoch_utc}-${index}`}>
                      <td>{record.epoch_utc}</td>
                      <td>{record.earth_moon_range_km}</td>
                      <td>{record.range_rate_km_s}</td>
                      <td>{record.one_way_down_leg_light_time_minutes}</td>
                      <td>{record.two_way_vacuum_light_time_seconds_derived}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          <div className="nasa-explorer-pagination">
            <span>Page {pagination?.page ?? 1} of {pagination?.total_pages ?? 0}</span>
            <div>
              <button type="button" onClick={() => onPageChange(pagination.page - 1)} disabled={!pagination?.has_previous || loading}>
                <ArrowLeft size={15} /> Previous
              </button>
              <button type="button" onClick={() => onPageChange(pagination.page + 1)} disabled={!pagination?.has_next || loading}>
                Next <ArrowRight size={15} />
              </button>
            </div>
          </div>
        </>
      ) : (
        <div className="nasa-explorer-chart-empty">No records are available for this dataset page.</div>
      )}
    </section>
  )
}

export default function NasaDataExplorer() {
  const [datasets, setDatasets] = useState([])
  const [selectedId, setSelectedId] = useState('')
  const [catalogLoading, setCatalogLoading] = useState(true)
  const [catalogError, setCatalogError] = useState('')
  const [metadata, setMetadata] = useState(null)
  const [summary, setSummary] = useState(null)
  const [detailLoading, setDetailLoading] = useState(true)
  const [detailErrors, setDetailErrors] = useState({})
  const [records, setRecords] = useState(null)
  const [pagination, setPagination] = useState(null)
  const [recordsLoading, setRecordsLoading] = useState(false)
  const [recordsError, setRecordsError] = useState('')
  const [page, setPage] = useState(1)
  const [detailReload, setDetailReload] = useState(0)
  const [recordsReload, setRecordsReload] = useState(0)
  const [aceVariable, setAceVariable] = useState('')
  const [stereoChannel, setStereoChannel] = useState('')

  const selectedDataset = datasets.find((dataset) => dataset.dataset_id === selectedId)
  const stereoChannels = useMemo(
    () => metadata?.processing_metadata?.channels || [],
    [metadata],
  )
  const variableOptions = useMemo(
    () => Object.entries(summary?.summary?.available_channel_coverage || {})
      .filter(([name, value]) => !name.startsWith('unc_') && value?.valid_records > 0)
      .map(([name, value]) => ({ name, description: value.description })),
    [summary?.summary?.available_channel_coverage],
  )
  const selectedAceVariable = variableOptions.some((option) => option.name === aceVariable)
    ? aceVariable
    : variableOptions[0]?.name || ''
  const selectedStereoChannel = stereoChannels.some((channel) => channel.name === stereoChannel)
    ? stereoChannel
    : stereoChannels[0]?.name || ''

  const loadCatalog = async () => {
    try {
      const response = await fetchDatasetsApi()
      setDatasets(response.datasets || [])
      setSelectedId((current) => current || response.datasets?.[0]?.dataset_id || '')
      setRecordsLoading(Boolean(response.datasets?.[0]?.record_access?.available))
    } catch (error) {
      setCatalogError(extractApiError(error, 'NASA dataset catalog could not be loaded.'))
    } finally {
      setCatalogLoading(false)
    }
  }

  const retryCatalog = () => {
    setCatalogLoading(true)
    setDetailLoading(true)
    setCatalogError('')
    loadCatalog()
  }

  useEffect(() => {
    let active = true
    window.scrollTo(0, 0)
    fetchDatasetsApi()
      .then((response) => {
        if (!active) return
        setDatasets(response.datasets || [])
        setSelectedId((current) => current || response.datasets?.[0]?.dataset_id || '')
        setRecordsLoading(Boolean(response.datasets?.[0]?.record_access?.available))
      })
      .catch((error) => {
        if (active) setCatalogError(extractApiError(error, 'NASA dataset catalog could not be loaded.'))
      })
      .finally(() => {
        if (active) setCatalogLoading(false)
      })
    return () => { active = false }
  }, [])

  useEffect(() => {
    if (!selectedId) return undefined
    let active = true
    Promise.allSettled([
      fetchDatasetMetadataApi(selectedId),
      fetchDatasetSummaryApi(selectedId),
    ]).then(([metadataResult, summaryResult]) => {
      if (!active) return
      const errors = {}
      if (metadataResult.status === 'fulfilled') setMetadata(metadataResult.value)
      else errors.metadata = extractApiError(metadataResult.reason, 'Dataset metadata could not be loaded.')
      if (summaryResult.status === 'fulfilled') setSummary(summaryResult.value)
      else errors.summary = extractApiError(summaryResult.reason, 'Dataset summary could not be loaded.')
      setDetailErrors(errors)
      setDetailLoading(false)
    })
    return () => { active = false }
  }, [selectedId, detailReload])

  useEffect(() => {
    if (!selectedId || !selectedDataset?.record_access?.available) {
      return undefined
    }
    let active = true
    fetchDatasetRecordsApi(selectedId, page, PAGE_SIZE)
      .then((response) => {
        if (!active) return
        setRecords(response.records || [])
        setPagination(response.pagination || null)
      })
      .catch((error) => {
        if (!active) return
        setRecords([])
        setPagination(null)
        setRecordsError(extractApiError(error, 'Dataset records could not be loaded.'))
      })
      .finally(() => {
        if (active) setRecordsLoading(false)
      })
    return () => { active = false }
  }, [selectedId, selectedDataset?.record_access?.available, page, recordsReload])

  const openDataset = (datasetId) => {
    setSelectedId(datasetId)
    setPage(1)
    setDetailLoading(true)
    setMetadata(null)
    setSummary(null)
    setRecords(null)
    setPagination(null)
    setRecordsError('')
    setRecordsLoading(Boolean(datasets.find((dataset) => dataset.dataset_id === datasetId)?.record_access?.available))
    setDetailReload((value) => value + 1)
    setRecordsReload((value) => value + 1)
    window.setTimeout(() => {
      document.getElementById('nasa-dataset-details')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }, 60)
  }

  const retryDetails = () => {
    setDetailLoading(true)
    setDetailReload((value) => value + 1)
  }

  const changeRecordsPage = (nextPage) => {
    setPage(nextPage)
    setRecordsLoading(true)
    setRecords([])
    setRecordsError('')
  }

  const retryRecords = () => {
    setRecordsLoading(true)
    setRecordsError('')
    setRecordsReload((value) => value + 1)
  }

  const selectedSummary = summary?.summary
  const summaryMetric = selectedId === 'jpl_horizons'
    ? selectedSummary?.two_way_vacuum_light_time_seconds_derived?.mean
    : selectedId === 'lola'
      ? selectedSummary?.height_m_relative_to_reference_radius_statistics?.height_m_mean
      : null
  const summaryMetricLabel = selectedId === 'jpl_horizons'
    ? 'Mean two-way vacuum light time (derived)'
    : selectedId === 'lola'
      ? 'Global mean height relative to reference radius'
      : ''
  const summaryMetricUnit = selectedId === 'jpl_horizons' ? 'seconds' : 'meters'
  const isUnavailable = selectedDataset?.availability?.status === 'unavailable'

  return (
    <>
      <Navbar />
      <main className="nasa-explorer-page">
        <div className="nasa-explorer-container">
          <header className="nasa-explorer-hero">
            <span className="nasa-explorer-kicker"><Satellite size={15} /> NASA ARCHIVE // DATA EXPLORER</span>
            <h1>Explore Real NASA Datasets</h1>
            <p>
              Browse the project’s processed NASA products, source coverage, and validated records.
              Archive observations and calculated ephemerides are clearly distinguished.
            </p>
            <div className="nasa-explorer-legend" aria-label="Data interpretation labels">
              <span className="nasa-data-tag real">REAL NASA DATA</span>
              <span className="nasa-data-tag computed">COMPUTED EPHEMERIS</span>
              <span className="nasa-data-tag derived">DERIVED VALUE</span>
              <span className="nasa-data-tag simulated">SIMULATED GAME CONSEQUENCE</span>
              <span className="nasa-explorer-legend-note">Game consequences are not shown in this explorer.</span>
            </div>
          </header>

          {catalogError && (
            <div className="nasa-explorer-alert" role="alert">
              <AlertTriangle size={18} />
              <div><strong>Dataset service unavailable</strong><p>{catalogError}</p></div>
              <button type="button" className="nasa-explorer-button" onClick={retryCatalog}>
                <RefreshCw size={15} /> Retry
              </button>
            </div>
          )}

          <section aria-labelledby="nasa-dataset-list-title">
            <div className="nasa-explorer-section-heading">
              <div>
                <span className="nasa-explorer-eyebrow">AVAILABLE ARCHIVES</span>
                <h2 id="nasa-dataset-list-title">NASA datasets</h2>
              </div>
              <span className="nasa-explorer-count">{datasets.length} datasets</span>
            </div>
            {catalogLoading && datasets.length === 0 ? (
              <div className="nasa-explorer-state"><Loader2 className="nasa-explorer-spin" size={25} /> Loading dataset catalog…</div>
            ) : datasets.length === 0 && !catalogError ? (
              <div className="nasa-explorer-state">No datasets are currently listed by the backend.</div>
            ) : (
              <div className="nasa-explorer-grid">
                {datasets.map((dataset) => (
                  <article className={`nasa-dataset-card${selectedId === dataset.dataset_id ? ' selected' : ''}`} key={dataset.dataset_id}>
                    <div className="nasa-dataset-card-top">
                      <span className="nasa-dataset-icon"><Database size={19} /></span>
                      <span className={`nasa-availability ${dataset.availability?.status === 'available' ? 'available' : 'unavailable'}`}>
                        <i /> {dataset.availability?.status === 'available' ? 'Available' : 'Unavailable'}
                      </span>
                    </div>
                    <span className="nasa-dataset-category">{dataset.category || 'NASA dataset'}</span>
                    <h3>{dataset.dataset_name}</h3>
                    <p className="nasa-dataset-source">{dataset.source?.organization || 'NASA source not listed'}</p>
                    <dl className="nasa-dataset-card-info">
                      <div><dt>Coverage</dt><dd>{dataset.coverage || 'Not specified'}</dd></div>
                      <div><dt>Measurements</dt><dd>{dataset.important_variables || 'See dataset metadata'}</dd></div>
                      <div><dt>Units</dt><dd>{dataset.units || 'See dataset metadata'}</dd></div>
                      <div><dt>Validation</dt><dd>{dataset.validation_status || 'Not specified'}</dd></div>
                    </dl>
                    <button
                      type="button"
                      className="nasa-explorer-card-button"
                      onClick={() => openDataset(dataset.dataset_id)}
                    >
                      View details <ArrowRight size={15} />
                    </button>
                  </article>
                ))}
              </div>
            )}
          </section>

          {selectedDataset && (
            <section id="nasa-dataset-details" className="nasa-explorer-details" aria-labelledby="nasa-dataset-detail-title">
              <div className="nasa-explorer-section-heading nasa-explorer-detail-heading">
                <div>
                  <span className="nasa-explorer-eyebrow">DATASET DETAILS</span>
                  <h2 id="nasa-dataset-detail-title">{metadata?.dataset_name || selectedDataset.dataset_name}</h2>
                </div>
                <span className={`nasa-data-tag ${metadata ? (metadata.data_type === 'computed_ephemeris' ? 'computed' : 'real') : ''}`}>
                  {metadata ? datasetLabel(metadata) : 'LOADING METADATA'}
                </span>
              </div>

              {detailLoading && !metadata && (
                <div className="nasa-explorer-inline-state"><Loader2 className="nasa-explorer-spin" size={18} /> Loading dataset details…</div>
              )}
              {isUnavailable && (
                <div className="nasa-explorer-alert" role="status">
                  <AlertTriangle size={18} />
                  Processed dataset files are unavailable. Showing catalog information where possible.
                </div>
              )}
              {(detailErrors.metadata || detailErrors.summary) && (
                <div className="nasa-explorer-alert" role="alert">
                  <AlertTriangle size={18} />
                  <div>
                    {detailErrors.metadata && <p>{detailErrors.metadata}</p>}
                    {detailErrors.summary && <p>{detailErrors.summary}</p>}
                  </div>
                  <button type="button" className="nasa-explorer-button"                   onClick={retryDetails}>
                    <RefreshCw size={15} /> Retry details
                  </button>
                </div>
              )}

              <div className="nasa-explorer-detail-grid">
                <article className="nasa-explorer-panel nasa-explorer-description">
                  <span className="nasa-explorer-eyebrow">SCIENTIFIC PURPOSE</span>
                  <p>{metadata?.scientific_purpose || selectedDataset.scientific_purpose || 'Purpose information is not available.'}</p>
                  <dl className="nasa-explorer-detail-facts">
                    <div><dt>Coverage</dt><dd>{metadata?.coverage || selectedDataset.coverage || 'Not specified'}</dd></div>
                    <div><dt>Geographic / spacecraft coverage</dt><dd>{metadata?.geographic_or_spacecraft_coverage || selectedDataset.geographic_or_spacecraft_coverage || 'Not specified'}</dd></div>
                    <div><dt>Units</dt><dd>{metadata?.units || selectedDataset.units || 'Not specified'}</dd></div>
                    <div><dt>Validation</dt><dd>{metadata?.validation_status || selectedDataset.validation_status || 'Not specified'}</dd></div>
                    <div>
                      <dt>Source</dt>
                      <dd>
                        {metadata?.source?.organization || selectedDataset.source?.organization || 'NASA source'}
                        {(metadata?.source?.urls || selectedDataset.source?.urls || []).map((url) => (
                          <a className="nasa-explorer-source-link" href={url} key={url} target="_blank" rel="noopener noreferrer">
                            Official source <ExternalLink size={13} />
                          </a>
                        ))}
                      </dd>
                    </div>
                  </dl>
                </article>

                <article className="nasa-explorer-panel nasa-explorer-limitations">
                  <span className="nasa-explorer-eyebrow">SCIENTIFIC LIMITATIONS</span>
                  <ul>
                    {(metadata?.scientific_limitations || selectedDataset.scientific_limitations || []).map((limitation) => (
                      <li key={limitation}>{limitation}</li>
                    ))}
                    {metadata?.data_type === 'computed_ephemeris' && (
                      <li>Forward Horizons values in this archived query are predictions, not observations.</li>
                    )}
                  </ul>
                  {metadata?.data_type === 'computed_ephemeris' && (
                    <span className="nasa-data-tag computed">COMPUTED EPHEMERIS</span>
                  )}
                  {metadata?.processing_metadata?.variables?.two_way_vacuum_light_time_seconds_derived && (
                    <p className="nasa-explorer-derived-note">
                      <span className="nasa-data-tag derived">DERIVED VALUE</span>
                      {' '}Two-way vacuum light time is calculated from the source one-way value; it is not total communication delay.
                    </p>
                  )}
                </article>
              </div>

              {summaryMetric !== null && summaryMetric !== undefined && (
                <div className="nasa-explorer-metric">
                  <span className="nasa-explorer-eyebrow">{summaryMetricLabel}</span>
                  <strong>{displayNumber(summaryMetric, 5)} <small>{summaryMetricUnit}</small></strong>
                  {selectedId === 'jpl_horizons' && <span className="nasa-data-tag derived">DERIVED VALUE</span>}
                  {selectedId === 'lola' && <span className="nasa-data-tag derived">DERIVED VALUE</span>}
                </div>
              )}

              {metadata?.processing_metadata && (
                <details className="nasa-explorer-processing">
                  <summary>Processing information and field definitions</summary>
                  <div className="nasa-explorer-processing-content">
                    <p>
                      Processed file: {(metadata.processed_files || [])[0] || 'Not listed'}.
                      {' '}The backend sidecar preserves processing, source, and validation details.
                    </p>
                    {metadata.processing_metadata.columns && (
                      <div className="nasa-explorer-tags">
                        {metadata.processing_metadata.columns.map((column) => (
                          <span key={column.output_name}>{column.output_name} ({column.unit})</span>
                        ))}
                      </div>
                    )}
                    {metadata.processing_metadata.variables && (
                      <div className="nasa-explorer-tags">
                        {Object.entries(metadata.processing_metadata.variables)
                          .slice(0, 24)
                          .map(([name, variable]) => (
                            <span key={name}>{name}{variable.units ? ` · ${variable.units}` : ''}</span>
                          ))}
                        {Object.keys(metadata.processing_metadata.variables).length > 24 && (
                          <span>See complete backend metadata for remaining variables.</span>
                        )}
                      </div>
                    )}
                    {metadata.processing_metadata.channels && (
                      <div className="nasa-explorer-tags">
                        {metadata.processing_metadata.channels.map((channel) => (
                          <span key={channel.name}>
                            {channel.particle} {channel.energy_min_MeV}–{channel.energy_max_MeV} MeV
                          </span>
                        ))}
                      </div>
                    )}
                    {metadata.processing_metadata.warnings?.map((warning) => (
                      <p className="nasa-explorer-warning" key={warning}>{warning}</p>
                    ))}
                    {metadata.processing_metadata.source_validation_warnings_preserved?.map((warning) => (
                      <p className="nasa-explorer-warning" key={warning}>{warning}</p>
                    ))}
                  </div>
                </details>
              )}

              {summary && (
                <SummaryStatistics datasetId={selectedId} summary={selectedSummary} />
              )}

              {summary && (
                <SummaryChart
                  dataset={metadata}
                  summary={selectedSummary}
                  records={records}
                  aceVariable={selectedAceVariable}
                  setAceVariable={setAceVariable}
                  stereoChannel={selectedStereoChannel}
                  setStereoChannel={setStereoChannel}
                  variableOptions={variableOptions}
                  stereoChannels={stereoChannels}
                />
              )}

              {metadata && (
                <RecordsTable
                  dataset={metadata}
                  records={records}
                  pagination={pagination}
                  loading={recordsLoading}
                  error={recordsError}
                  onPageChange={changeRecordsPage}
                  onRetry={retryRecords}
                  aceVariable={selectedAceVariable}
                  stereoChannels={stereoChannels}
                  stereoChannel={selectedStereoChannel}
                />
              )}
            </section>
          )}

          <aside className="nasa-explorer-footer-note">
            <span className="nasa-data-tag real">REAL NASA DATA</span>
            <span>Archive products are historical observations or computed data with their stated coverage. They are not live mission telemetry.</span>
          </aside>
        </div>
      </main>
      <Footer />
    </>
  )
}
