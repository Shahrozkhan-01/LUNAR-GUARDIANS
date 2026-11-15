import { useEffect, useState } from 'react'
import { Volume2, VolumeX } from 'lucide-react'
import { isSoundEnabled, playSound, setSoundEnabled } from '../services/soundEffects.js'

export default function SoundEffects({ showControl = true, listen = true }) {
  const [enabled, setEnabled] = useState(isSoundEnabled)

  useEffect(() => {
    const onSoundChange = (event) => setEnabled(Boolean(event.detail?.enabled))
    const onPointerDown = (event) => {
      if (event.target.closest('button, a, [role="button"]')) playSound('click')
    }
    const onPointerOver = (event) => {
      const interactive = event.target.closest('button, a, [role="button"]')
      if (!interactive || interactive.disabled) return
      if (event.relatedTarget instanceof Node && interactive.contains(event.relatedTarget)) {
        return
      }
      playSound('hover')
    }
    if (listen) {
      window.addEventListener('lunar-guardians-sound-change', onSoundChange)
      document.addEventListener('pointerdown', onPointerDown, true)
      document.addEventListener('pointerover', onPointerOver, true)
    }
    return () => {
      if (listen) {
        window.removeEventListener('lunar-guardians-sound-change', onSoundChange)
        document.removeEventListener('pointerdown', onPointerDown, true)
        document.removeEventListener('pointerover', onPointerOver, true)
      }
    }
  }, [listen])

  const toggle = () => {
    const nextEnabled = !enabled
    setEnabled(nextEnabled)
    setSoundEnabled(nextEnabled)
    if (nextEnabled) playSound('success')
  }

  if (!showControl) return null

  return (
    <button
      type="button"
      className="sound-toggle"
      onClick={toggle}
      aria-label={enabled ? 'Turn sound effects off' : 'Turn sound effects on'}
      aria-pressed={enabled}
      title={enabled ? 'Sound effects on' : 'Sound effects off'}
    >
      {enabled ? <Volume2 size={16} /> : <VolumeX size={16} />}
      <span>{enabled ? 'SOUND ON' : 'SOUND OFF'}</span>
    </button>
  )
}
