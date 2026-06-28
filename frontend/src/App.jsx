import { useState, useEffect } from 'react'
import LandingPage from './pages/LandingPage.jsx'
import QuestionnairePage from './pages/QuestionnairePage.jsx'

const viewForPath = (path) =>
  path === '/questionnaire' ? 'questionnaire' : 'landing'

export default function App() {
  const [view, setView] = useState(viewForPath(window.location.pathname))

  // Keep the view in sync with the browser back/forward buttons.
  useEffect(() => {
    const onPop = () => setView(viewForPath(window.location.pathname))
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])

  const navigate = (next) => {
    const path = next === 'questionnaire' ? '/questionnaire' : '/'
    if (window.location.pathname !== path) {
      window.history.pushState({}, '', path)
    }
    setView(next)
    window.scrollTo(0, 0)
  }

  return view === 'questionnaire' ? (
    <QuestionnairePage onNavigate={navigate} />
  ) : (
    <LandingPage onNavigate={navigate} />
  )
}
