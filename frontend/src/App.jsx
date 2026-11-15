import { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import MissionProvider from './context/MissionContext.jsx'
import Home from './pages/Home.jsx'
import MissionSetup from './pages/MissionSetup.jsx'
import MissionControl from './pages/MissionControl.jsx'
import Stars from './components/Stars.jsx'
import SoundEffects from './components/SoundEffects.jsx'

const NasaDataExplorer = lazy(() => import('./pages/NasaDataExplorer.jsx'))

function App() {
  return (
    <MissionProvider>
      <Stars />
      <SoundEffects showControl={false} />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/mission-setup" element={<MissionSetup />} />
        <Route path="/mission-control" element={<MissionControl />} />
        <Route
          path="/nasa-data"
          element={(
            <Suspense fallback={<div role="status" style={{ padding: '120px 24px', textAlign: 'center' }}>Loading NASA Data Explorer…</div>}>
              <NasaDataExplorer />
            </Suspense>
          )}
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </MissionProvider>
  )
}

export default App
