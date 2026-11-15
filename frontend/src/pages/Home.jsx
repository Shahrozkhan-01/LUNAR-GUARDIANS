import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import Navbar from '../components/Navbar.jsx'
import Hero from '../components/Hero.jsx'
import { MissionFeaturesSection } from '../components/FeatureCard.jsx'
import HowToPlay from '../components/HowToPlay.jsx'
import NasaScience from '../components/NasaScience.jsx'
import Footer from '../components/Footer.jsx'

export default function Home() {
  const location = useLocation()

  useEffect(() => {
    const targetId = location.state?.scrollTo
    if (targetId) {
      const timer = setTimeout(() => {
        const el = document.getElementById(targetId)
        if (el) {
          el.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }
      }, 80)
      return () => clearTimeout(timer)
    }
  }, [location.state])

  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <MissionFeaturesSection />
        <HowToPlay />
        <NasaScience />
      </main>
      <Footer />
    </>
  )
}
