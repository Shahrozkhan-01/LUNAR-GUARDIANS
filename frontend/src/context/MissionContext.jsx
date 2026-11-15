import { useState, useEffect, useCallback, useMemo } from 'react'
import {
  MissionContext,
  MISSION_ID_STORAGE_KEY,
  SETUP_PREFS_STORAGE_KEY,
} from './missionConstants.js'
import {
  startMissionApi,
  fetchMissionStateApi,
  executeActionApi,
  advanceMissionDayApi,
  updatePowerAllocationApi,
  extractApiError,
} from '../services/gameApi.js'
import { playSound } from '../services/soundEffects.js'

function loadSavedSetupPrefs() {
  try {
    const raw = sessionStorage.getItem(SETUP_PREFS_STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export default function MissionProvider({ children }) {
  const [missionId, setMissionId] = useState(() => {
    try {
      return sessionStorage.getItem(MISSION_ID_STORAGE_KEY) || null
    } catch {
      return null
    }
  })

  const [setupPrefs, setSetupPrefs] = useState(loadSavedSetupPrefs)
  const [gameState, setGameState] = useState(null)
  const [isPaused, setIsPaused] = useState(false)

  const [isLoadingMission, setIsLoadingMission] = useState(false)
  const [isAdvancingDay, setIsAdvancingDay] = useState(false)
  const [pendingActionId, setPendingActionId] = useState(null)
  const [isSavingPower, setIsSavingPower] = useState(false)

  const [apiError, setApiError] = useState(null)
  const [feedbackBanner, setFeedbackBanner] = useState(null)

  // Hydrate authoritative game state from backend when missionId exists on page load/refresh
  useEffect(() => {
    let cancelled = false
    async function hydrateFromBackend() {
      if (!missionId || gameState?.mission_id === missionId) return
      setIsLoadingMission(true)
      setApiError(null)
      try {
        const data = await fetchMissionStateApi(missionId)
        if (!cancelled) {
          setGameState(data)
        }
      } catch (err) {
        if (!cancelled) {
          // If backend restarted and in-memory mission expired, clear stale ID gracefully
          if (err?.response?.status === 404) {
            sessionStorage.removeItem(MISSION_ID_STORAGE_KEY)
            setMissionId(null)
            setGameState(null)
          } else {
            setApiError(extractApiError(err))
          }
        }
      } finally {
        if (!cancelled) {
          setIsLoadingMission(false)
        }
      }
    }
    hydrateFromBackend()
    return () => {
      cancelled = true
    }
  }, [missionId, gameState?.mission_id])

  const startNewMission = useCallback(async (config) => {
    setIsLoadingMission(true)
    setApiError(null)
    setFeedbackBanner(null)
    try {
      const payload = {
        destination: config.destination || 'lunar-outpost',
        difficulty: config.difficulty,
        crew_size: config.crewSize,
        duration: config.duration,
        mission_name: 'Lunar Outpost Alpha',
        deterministic: Boolean(config.deterministic),
        enable_random_events: config.enableRandomEvents !== false,
      }
      const createdState = await startMissionApi(payload)
      sessionStorage.setItem(MISSION_ID_STORAGE_KEY, createdState.mission_id)
      sessionStorage.setItem(SETUP_PREFS_STORAGE_KEY, JSON.stringify(config))
      setSetupPrefs(config)
      setMissionId(createdState.mission_id)
      setGameState(createdState)
      setIsPaused(false)
      setFeedbackBanner({
        tone: 'info',
        title: 'Mission Initialized!',
        message: `Commanding ${createdState.crew_size} astronauts for ${createdState.duration} simulated days.`,
        educational: createdState.educational_tips?.[0] || null,
      })
      playSound('launch')
      return createdState
    } catch (err) {
      const msg = extractApiError(err, 'Failed to initialize mission on the backend server.')
      setApiError(msg)
      throw new Error(msg)
    } finally {
      setIsLoadingMission(false)
    }
  }, [])

  const advanceDay = useCallback(async () => {
    if (!missionId || isPaused || isAdvancingDay) return null
    setIsAdvancingDay(true)
    setApiError(null)
    try {
      const resp = await advanceMissionDayApi(missionId)
      setGameState(resp.game_state)
      setFeedbackBanner({
        tone: resp.game_state.mission_status === 'Mission Failed' ? 'warning' : 'success',
        title:
          resp.game_state.mission_status === 'In Progress'
            ? `Day ${resp.game_state.current_day} Briefing`
            : resp.game_state.mission_status,
        message: resp.day_summary,
        educational: resp.educational_notes?.[0] || null,
      })
      playSound(
        resp.game_state.mission_status === 'Mission Failed' ? 'warning' : 'success'
      )
      return resp.game_state
    } catch (err) {
      const msg = extractApiError(err, 'Could not advance to the next mission day.')
      setApiError(msg)
      return null
    } finally {
      setIsAdvancingDay(false)
    }
  }, [missionId, isPaused, isAdvancingDay])

  const performAction = useCallback(
    async (actionId, extra = {}) => {
      if (!missionId || isPaused || pendingActionId) return null
      setPendingActionId(actionId)
      setApiError(null)
      try {
        const resp = await executeActionApi(missionId, {
          action_id: actionId,
          ...extra,
        })
        setGameState(resp.game_state)
        setFeedbackBanner({
          tone: 'action',
          title: resp.action_name,
          message: resp.feedback_message,
          educational: resp.educational_note,
        })
        playSound('success')
        return resp
      } catch (err) {
        const msg = extractApiError(err, 'Action could not be executed.')
        setApiError(msg)
        return null
      } finally {
        setPendingActionId(null)
      }
    },
    [missionId, isPaused, pendingActionId]
  )

  const savePowerAllocation = useCallback(
    async (allocationPayload) => {
      if (!missionId || isPaused || isSavingPower) return null
      setIsSavingPower(true)
      setApiError(null)
      try {
        const updated = await updatePowerAllocationApi(missionId, allocationPayload)
        setGameState(updated)
        setFeedbackBanner({
          tone: 'info',
          title: 'Power Grid Updated',
          message: `Electricity distributed across outpost modules (${Math.round(
            allocationPayload.life_support +
              allocationPayload.radiation_shelter +
              allocationPayload.greenhouse +
              allocationPayload.communication +
              allocationPayload.scientific_research
          )} / ${updated.resources.power} units).`,
          educational:
            updated.educational_tips?.[0] ||
            'Life Support always has top priority if battery power runs low!',
        })
        return updated
      } catch (err) {
        const msg = extractApiError(err, 'Power allocation validation failed.')
        setApiError(msg)
        return null
      } finally {
        setIsSavingPower(false)
      }
    },
    [missionId, isPaused, isSavingPower]
  )

  const togglePause = useCallback(() => {
    setIsPaused((prev) => !prev)
  }, [])

  const clearApiError = useCallback(() => {
    setApiError(null)
  }, [])

  const value = useMemo(
    () => ({
      missionId,
      setupPrefs,
      gameState,
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
    }),
    [
      missionId,
      setupPrefs,
      gameState,
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
    ]
  )

  return <MissionContext.Provider value={value}>{children}</MissionContext.Provider>
}
