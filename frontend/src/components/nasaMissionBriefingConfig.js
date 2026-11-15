export const MISSION_BRIEFING_PRESETS = [
  {
    id: 'south_polar_exploration',
    title: 'South Polar Exploration',
    objective: 'Plan an outpost expedition using historical surface-environment context and broad regional terrain data.',
    datasets: ['diviner', 'lola'],
    background: 'Compare archived south-polar brightness temperatures with global elevation context when discussing habitat, power, and exploration planning.',
    limitations: [
      'Diviner brightness temperature is historical remote-sensing data, not live habitat or air temperature.',
      'LOLA is broad-scale elevation context, not detailed landing-site hazard information.',
    ],
    challenge: 'Which additional local measurements would you want before choosing a precise habitat or landing location?',
  },
  {
    id: 'space_weather_preparedness',
    title: 'Space Weather Preparedness',
    objective: 'Explore how spacecraft instruments measure energetic particles and discuss what additional information a crew would need.',
    datasets: ['ace_epam', 'stereo_impact'],
    background: 'Compare the archived ACE EPAM and STEREO-A channel examples as separate historical spacecraft datasets. Their measurement dates do not describe one simultaneous event. Use them for radiation-protection education, not dose estimates.',
    limitations: [
      'ACE measurements are from the ACE spacecraft near Sun–Earth L1, not the lunar surface.',
      'STEREO-A measurements are from STEREO-A, not the Moon.',
      'Neither dataset measures astronaut radiation dose; no dose is calculated here.',
    ],
    challenge: 'What location, timing, shielding, and dosimetry information would be needed before assessing crew exposure?',
  },
  {
    id: 'communication_navigation',
    title: 'Communication and Navigation',
    objective: 'Use a computed Earth–Moon ephemeris to distinguish one-way light time from an idealized two-way vacuum calculation.',
    datasets: ['jpl_horizons'],
    background: 'Review the archived Earth–Moon range and down-leg light-time values at their UTC epochs, then consider how distance affects message exchange.',
    limitations: [
      'Horizons values are computed ephemerides; forward epochs in the archived query are predictions, not observations.',
      'Two-way vacuum light time is mathematically derived from the one-way value.',
      'Network, equipment, routing, and processing delays are not included.',
    ],
    challenge: 'How would you explain the difference between ideal light travel time and a complete operational communication delay?',
  },
]
