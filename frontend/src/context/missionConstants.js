import { createContext, useContext } from 'react'

export const MISSION_ID_STORAGE_KEY = 'lunar_guardians_active_mission_id'
export const SETUP_PREFS_STORAGE_KEY = 'lunar_guardians_setup_prefs_v2'

export const DESTINATIONS = [
  {
    id: 'lunar-outpost',
    name: 'Lunar Outpost',
    subtitle: 'South Pole — Shackleton Rim',
    status: 'Available',
    available: true,
    description: 'Primary playable mission. Command a pressurized lunar base with access to sunlit ridges and polar craters.',
  },
  {
    id: 'mars-outpost',
    name: 'Mars Outpost',
    subtitle: 'Jezero Crater — Red Planet',
    status: 'Coming Soon',
    available: false,
    description: 'Deep-space planetary expedition featuring dust storms and long-delay communications. Unlocks in a future expansion.',
  },
]

export const DIFFICULTIES = [
  {
    id: 'explorer',
    name: 'Explorer',
    tagline: 'Beginner Friendly',
    description: 'More starting protection (65 Shield, +10 Science) and gentler daily consumption.',
    accent: '#22c55e',
    previewText: '100 Vital Units • 65 Shield • Milder Events',
  },
  {
    id: 'commander',
    name: 'Commander',
    tagline: 'Standard Training',
    description: 'Balanced starting reserves (100 O2/H2O/Power/Food, 50 Shield) and standard challenges.',
    accent: '#00e5ff',
    previewText: '100 Vital Units • 50 Shield • Balanced Ops',
  },
  {
    id: 'expert',
    name: 'Expert',
    tagline: 'Advanced Survival',
    description: 'Tighter starting reserves (85 Vital Units, 40 Shield) and tougher simulated events.',
    accent: '#ff6b35',
    previewText: '85 Vital Units • 40 Shield • High Challenge',
  },
]

export const CREW_OPTIONS = [
  { count: 2, label: '2 Astronauts', subtitle: 'Low daily oxygen, water & food demand' },
  { count: 4, label: '4 Astronauts', subtitle: 'Balanced outpost resource consumption' },
  { count: 6, label: '6 Astronauts', subtitle: 'High daily life-support & food demand' },
]

export const DURATION_OPTIONS = [
  { days: 5, label: '5 Days', subtitle: 'Short Training Rotation' },
  { days: 10, label: '10 Days', subtitle: 'Standard Lunar Expedition' },
  { days: 15, label: '15 Days', subtitle: 'Extended Survival Campaign' },
]

export const SETUP_OUTPOST_SYSTEMS = [
  {
    id: 'life-support',
    name: 'Life Support',
    code: 'SYS-01',
    summary: 'Highest-priority module! Produces breathable oxygen and powers air & water recycling.',
    status: 'PRIORITY #1',
  },
  {
    id: 'solar-power',
    name: 'Solar Power',
    code: 'SYS-02',
    summary: 'Generates daily electricity from sunlight; keep panels clean of lunar dust.',
    status: 'READY',
  },
  {
    id: 'radiation-shelter',
    name: 'Radiation Shelter',
    code: 'SYS-03',
    summary: 'Uses electricity to build Shield Protection and guard astronauts during solar storms.',
    status: 'READY',
  },
  {
    id: 'greenhouse',
    name: 'Greenhouse',
    code: 'SYS-04',
    summary: 'Uses water and electricity to harvest +18 fresh Food every 2 growth days.',
    status: 'READY',
  },
]

export const SYSTEM_MODALS_DATA = {
  'life-support': {
    id: 'life-support',
    name: 'Life Support',
    code: 'SYS-01 // HIGHEST PRIORITY',
    status: 'Operational Priority #1',
    accent: '#00e5ff',
    overview:
      'On the Moon, there is no breathable air! Life Support produces oxygen and runs both Oxygen Recycling and Water Recovery. It always receives electricity first before non-essential modules.',
    educationalFact:
      'Astronauts recycle cabin air and water every day so fewer heavy supply rockets have to launch from Earth!',
    upcomingControls: [
      'Keep Life Support allocated at 15+ Power so Oxygen & Water Recycling stay active.',
      'Use "Activate Oxygen Recycling" or "Activate Water Recovery" for immediate boosts.',
      'Larger crews (4 or 6 astronauts) breathe more oxygen and drink more water each day.',
    ],
  },
  'power-allocation': {
    id: 'power-allocation',
    name: 'Power Allocation',
    code: 'SYS-02 // SOLAR ELECTRICAL GRID',
    status: 'Interactive Grid Active',
    accent: '#38bdf8',
    overview:
      'Solar panels recharge your outpost battery each day. Use the Power Allocation sliders to divide available electricity across Life Support, Radiation Shelter, Greenhouse, Communication, and Scientific Research.',
    educationalFact:
      'Lunar dust sticks to solar panels with static electricity! Use "Repair Solar Panels" if dust lowers your solar efficiency.',
    upcomingControls: [
      'Total allocated electricity can never exceed your available Power.',
      'If battery power drops low, lower-priority systems like Research shut down first.',
      'Engage "Emergency Conservation Mode" to cut non-essential power use in half for 2 days.',
    ],
  },
  'radiation-shelter': {
    id: 'radiation-shelter',
    name: 'Radiation Shelter',
    code: 'SYS-03 // CREW PROTECTION BAY',
    status: 'Priority #2 Protection',
    accent: '#ff6b35',
    overview:
      'Because the Moon lacks a thick atmosphere, solar storms can increase crew radiation exposure. Energizing the Radiation Shelter builds Shield Protection and keeps your astronauts safe!',
    educationalFact:
      'Engineers design lunar shelters using thick regolith bags and water tanks around crew walls to absorb energetic particles.',
    upcomingControls: [
      'Click "Activate Radiation Shelter" (+15 Shield for 3 days) when a Solar Storm Warning appears.',
      'Requires 10 Power—and automatically pauses Scientific Research if electricity is tight.',
      'Keep shelter power funded (>= 12 units) to prevent passive shield decay.',
    ],
  },
  greenhouse: {
    id: 'greenhouse',
    name: 'Greenhouse',
    code: 'SYS-04 // LUNAR HYDROPONICS',
    status: '2-Day Harvest Cycle',
    accent: '#22c55e',
    overview:
      'Your hydroponic Greenhouse grows nutritious crops using LED grow-lights and recycled water. Every 2 powered and watered growth days, your crew harvests +18 Food!',
    educationalFact:
      'Space botanists have grown leafy greens, radishes, and dwarf tomatoes in spaceflight growth chambers!',
    upcomingControls: [
      'Allocate at least 12 Power to Greenhouse and keep clean Water available.',
      'Track crop progress (0/2 -> 1/2 -> Harvest!) right on the dashboard.',
      'Repair greenhouse valves promptly if an equipment fault occurs.',
    ],
  },
  communication: {
    id: 'communication',
    name: 'Communication',
    code: 'SYS-05 // EARTH TELEMETRY LINK',
    status: 'Telemetry & Science Bonus',
    accent: '#a855f7',
    overview:
      'The high-gain Communication Antenna keeps your lunar base linked with Earth Mission Control, earning +3 bonus Science Points every day it receives at least 8 Power.',
    educationalFact:
      'Radio waves travel at the speed of light—crossing the 384,400 km gap between Earth and the Moon in ~1.3 seconds!',
    upcomingControls: [
      'Maintain 8+ Power on Communication for daily telemetry Science Points.',
      'Realign dish motors if thermal shifts cause a Communication Interruption.',
      'Future Phase: Live NASA DONKI space weather advisories will arrive here.',
    ],
  },
}

export const CREW_VISOR_COLORS = [
  '#00e5ff',
  '#38bdf8',
  '#22c55e',
  '#facc15',
  '#a855f7',
  '#ff6b35',
]

export const MissionContext = createContext(null)

export function useMission() {
  const ctx = useContext(MissionContext)
  if (!ctx) {
    throw new Error('useMission must be used within a MissionProvider')
  }
  return ctx
}
