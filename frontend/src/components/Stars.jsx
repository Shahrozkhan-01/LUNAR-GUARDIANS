const STAR_DATA = Array.from({ length: 110 }, (_, i) => {
  const s1 = ((i * 73 + 19) % 997) / 997
  const s2 = ((i * 197 + 53) % 991) / 991
  const s3 = ((i * 311 + 101) % 983) / 983
  return {
    id: i,
    left: `${(s1 * 100).toFixed(2)}%`,
    top: `${(s2 * 100).toFixed(2)}%`,
    size: (s3 * 1.8 + 1).toFixed(2),
    duration: `${(s1 * 3.8 + 2.2).toFixed(2)}s`,
    delay: `${(s2 * 4.5).toFixed(2)}s`,
    maxOpacity: (s3 * 0.55 + 0.25).toFixed(2),
  }
})

export default function Stars() {
  return (
    <div className="stars-container" aria-hidden="true">
      <div className="celestial-moon" />
      <div className="celestial-saturn">
        <span />
      </div>
      <div className="celestial-mars" />
      {STAR_DATA.map((star) => (
        <div
          key={star.id}
          className="star"
          style={{
            left: star.left,
            top: star.top,
            width: `${star.size}px`,
            height: `${star.size}px`,
            '--duration': star.duration,
            '--max-opacity': star.maxOpacity,
            animationDelay: star.delay,
          }}
        />
      ))}
    </div>
  )
}
