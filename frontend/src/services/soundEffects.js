const SOUND_STORAGE_KEY = 'lunar-guardians-sound-enabled'
let audioContext = null

export function isSoundEnabled() {
  try {
    return window.localStorage.getItem(SOUND_STORAGE_KEY) === 'true'
  } catch {
    return false
  }
}

export function setSoundEnabled(enabled) {
  try {
    window.localStorage.setItem(SOUND_STORAGE_KEY, String(enabled))
  } catch {
    // Audio remains usable for the current page even if storage is unavailable.
  }
  window.dispatchEvent(new CustomEvent('lunar-guardians-sound-change', {
    detail: { enabled },
  }))
}

export function playSound(type = 'click') {
  if (!isSoundEnabled()) return

  try {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext
    if (!AudioContextClass) return
    if (!audioContext || audioContext.state === 'closed') {
      audioContext = new AudioContextClass()
    }
    const context = audioContext
    const renderTone = () => {
      const oscillator = context.createOscillator()
      const gain = context.createGain()
      const settings = {
        hover: [620, 0.055, 0.045],
        click: [520, 0.09, 0.07],
        select: [580, 0.12, 0.065],
        success: [740, 0.16, 0.08],
        warning: [220, 0.2, 0.07],
        launch: [320, 0.28, 0.08],
        complete: [660, 0.3, 0.08],
      }[type] || [520, 0.08, 0.07]
      const [frequency, duration, volume] = settings

      oscillator.type = type === 'warning' ? 'triangle' : 'sine'
      oscillator.frequency.setValueAtTime(frequency, context.currentTime)
      if (type === 'launch') {
        oscillator.frequency.exponentialRampToValueAtTime(
          frequency * 1.8,
          context.currentTime + duration
        )
      }
      gain.gain.setValueAtTime(volume, context.currentTime)
      gain.gain.exponentialRampToValueAtTime(
        0.001,
        context.currentTime + duration
      )
      oscillator.connect(gain)
      gain.connect(context.destination)
      oscillator.start()
      oscillator.stop(context.currentTime + duration)
    }

    if (context.state === 'suspended') {
      context.resume().then(renderTone).catch(() => {})
    } else {
      renderTone()
    }
  } catch {
    // Audio is an enhancement; unsupported or blocked audio must not affect play.
  }
}
