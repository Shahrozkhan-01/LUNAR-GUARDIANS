import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

export function extractApiError(error, fallback = 'Unable to reach Mission Control server.') {
  if (error?.response?.data?.detail) {
    const detail = error.response.data.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) {
      return detail.map((d) => d.msg || JSON.stringify(d)).join('; ')
    }
    if (typeof detail === 'object' && typeof detail.message === 'string') {
      return detail.message
    }
  }
  if (error?.code === 'ERR_NETWORK') {
    return `Cannot connect to the FastAPI simulation backend (${API_BASE_URL}). Please make sure the backend server is running.`
  }
  return error?.message || fallback
}

export async function startMissionApi(configPayload) {
  const response = await apiClient.post('/api/game/start', configPayload)
  return response.data
}

export async function fetchMissionStateApi(missionId) {
  const response = await apiClient.get(`/api/game/${missionId}`)
  return response.data
}

export async function executeActionApi(missionId, actionPayload) {
  const response = await apiClient.post(`/api/game/${missionId}/action`, actionPayload)
  return response.data
}

export async function advanceMissionDayApi(missionId) {
  const response = await apiClient.post(`/api/game/${missionId}/advance`)
  return response.data
}

export async function fetchMissionEventsApi(missionId) {
  const response = await apiClient.get(`/api/game/${missionId}/events`)
  return response.data
}

export async function updatePowerAllocationApi(missionId, powerPayload) {
  const response = await apiClient.post(`/api/game/${missionId}/power`, powerPayload)
  return response.data
}

export async function fetchNasaDashboardApi(refresh = false) {
  const statusResponse = await apiClient.get('/api/nasa/status', {
    params: { refresh },
    timeout: 45000,
  })
  const status = statusResponse.data
  if (status.connection_status === 'unavailable') {
    const eventErrors = Object.fromEntries(
      Object.entries(status.endpoint_status || {})
        .filter(([, feed]) => feed.error)
        .map(([eventType, feed]) => [eventType, feed.error]),
    )
    return {
      ...status,
      events_by_type: { FLR: [], SEP: [] },
      event_errors: eventErrors,
    }
  }

  const [flareResult, sepResult] = await Promise.allSettled([
    apiClient.get('/api/nasa/flares', { timeout: 45000 }),
    apiClient.get('/api/nasa/sep', { timeout: 45000 }),
  ])
  const eventsByType = {
    FLR: flareResult.status === 'fulfilled' ? flareResult.value.data.events : [],
    SEP: sepResult.status === 'fulfilled' ? sepResult.value.data.events : [],
  }
  const eventErrors = {}
  if (flareResult.status === 'rejected') {
    eventErrors.FLR = extractApiError(flareResult.reason, 'Solar flare data is unavailable.')
  }
  if (sepResult.status === 'rejected') {
    eventErrors.SEP = extractApiError(sepResult.reason, 'Solar particle data is unavailable.')
  }

  return { ...status, events_by_type: eventsByType, event_errors: eventErrors }
}

export async function fetchDatasetsApi() {
  const response = await apiClient.get('/api/datasets')
  return response.data
}

export async function fetchDatasetMetadataApi(datasetId) {
  const response = await apiClient.get(`/api/datasets/${encodeURIComponent(datasetId)}/metadata`)
  return response.data
}

export async function fetchDatasetSummaryApi(datasetId) {
  const response = await apiClient.get(`/api/datasets/${encodeURIComponent(datasetId)}/summary`)
  return response.data
}

export async function fetchDatasetRecordsApi(datasetId, page = 1, pageSize = 20) {
  const response = await apiClient.get(`/api/datasets/${encodeURIComponent(datasetId)}/records`, {
    params: { page, page_size: pageSize },
  })
  return response.data
}
