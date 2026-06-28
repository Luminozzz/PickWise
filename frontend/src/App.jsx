import { useState, useEffect } from 'react'
import LandingPage from './pages/LandingPage.jsx'
import QuestionnairePage from './pages/QuestionnairePage.jsx'
import RecommendationsPage from './pages/RecommendationsPage.jsx'

const PATHS = {
  questionnaire: '/questionnaire',
  recommendations: '/recommendations',
  landing: '/',
}

const viewForPath = (path) => {
  if (path === '/questionnaire') return 'questionnaire'
  if (path === '/recommendations') return 'recommendations'
  return 'landing'
}

// The "profile" = the questionnaire answers that produced a recommendation.
function loadAnswers() {
  try {
    return JSON.parse(sessionStorage.getItem('pickwise_answers') || 'null')
  } catch {
    return null
  }
}

export default function App() {
  const [view, setView] = useState(viewForPath(window.location.pathname))
  const [answers, setAnswers] = useState(loadAnswers)

  // Keep the view in sync with the browser back/forward buttons.
  useEffect(() => {
    const onPop = () => setView(viewForPath(window.location.pathname))
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])

  const navigate = (next, payload) => {
    if (payload !== undefined) {
      setAnswers(payload)
      try {
        if (payload === null) sessionStorage.removeItem('pickwise_answers')
        else sessionStorage.setItem('pickwise_answers', JSON.stringify(payload))
      } catch {
        /* ignore storage errors */
      }
    }
    const path = PATHS[next] || '/'
    if (window.location.pathname !== path) {
      window.history.pushState({}, '', path)
    }
    setView(next)
    window.scrollTo(0, 0)
  }

  // Recommendations require a profile; without one, send them to the quiz.
  useEffect(() => {
    if (view === 'recommendations' && !answers) {
      navigate('questionnaire')
    }
  }, [view, answers])

  if (view === 'questionnaire') {
    return <QuestionnairePage onNavigate={navigate} />
  }
  if (view === 'recommendations') {
    if (!answers) return null // redirecting to the questionnaire
    return <RecommendationsPage answers={answers} onNavigate={navigate} />
  }
  return <LandingPage onNavigate={navigate} />
}
