import { useState, useEffect } from 'react'
import LandingPage from './pages/LandingPage.jsx'
import QuestionnairePage from './pages/QuestionnairePage.jsx'
import RecommendationsPage from './pages/RecommendationsPage.jsx'
import ProfilePage from './pages/ProfilePage.jsx'
import { createProfile, getProfile, updateProfile } from './api.js'

const PATHS = {
  questionnaire: '/questionnaire',
  recommendations: '/recommendations',
  profile: '/profile',
  landing: '/',
}

const viewForPath = (path) => {
  if (path === '/questionnaire') return 'questionnaire'
  if (path === '/recommendations') return 'recommendations'
  if (path === '/profile') return 'profile'
  return 'landing'
}

const PROFILE_KEY = 'pickwise_profile_id'

// The "profile" = the questionnaire answers that produced a recommendation.
function loadAnswers() {
  try {
    return JSON.parse(sessionStorage.getItem('pickwise_answers') || 'null')
  } catch {
    return null
  }
}

function loadProfileId() {
  try {
    return localStorage.getItem(PROFILE_KEY)
  } catch {
    return null
  }
}

export default function App() {
  const [view, setView] = useState(viewForPath(window.location.pathname))
  const [answers, setAnswers] = useState(loadAnswers)
  const [profileId, setProfileId] = useState(loadProfileId)
  const [hydrationError, setHydrationError] = useState(null)

  // Keep the in-memory answers and their sessionStorage copy in sync.
  const applyAnswers = (next) => {
    setAnswers(next)
    try {
      if (next === null) sessionStorage.removeItem('pickwise_answers')
      else sessionStorage.setItem('pickwise_answers', JSON.stringify(next))
    } catch {
      /* ignore storage errors */
    }
  }

  // Persist answers to the backend: POST the first time (remember the id), PUT after.
  const saveProfile = async (nextAnswers) => {
    if (profileId) return updateProfile(profileId, nextAnswers)
    const created = await createProfile(nextAnswers)
    setProfileId(created.id)
    try {
      localStorage.setItem(PROFILE_KEY, created.id)
    } catch {
      /* ignore storage errors */
    }
    return created
  }

  // Profile "Save changes": persist AND adopt the edits as the live answers.
  const handleSaveProfile = async (nextAnswers) => {
    const saved = await saveProfile(nextAnswers)
    applyAnswers(nextAnswers)
    return saved
  }

  const retryHydration = () => {
    setHydrationError(null)
    const id = profileId
    if (!id) { navigate('questionnaire'); return }
    getProfile(id)
      .then((p) => {
        if (p) applyAnswers(p.answers || {})
        else {
          setProfileId(null)
          try { localStorage.removeItem(PROFILE_KEY) } catch { /* ignore */ }
          navigate('questionnaire')
        }
      })
      .catch(() => setHydrationError(true))
  }

  // Keep the view in sync with the browser back/forward buttons.
  useEffect(() => {
    const onPop = () => setView(viewForPath(window.location.pathname))
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])

  // Returning visitor: hydrate answers from the saved profile if we don't have them.
  useEffect(() => {
    if (!profileId || answers) return
    let active = true
    getProfile(profileId)
      .then((p) => {
        if (!active) return
        if (p) applyAnswers(p.answers || {})
        else {
          // stale id (profile no longer exists) — forget it
          setProfileId(null)
          try {
            localStorage.removeItem(PROFILE_KEY)
          } catch {
            /* ignore */
          }
        }
      })
      .catch(() => { if (active) setHydrationError(true) })
    return () => {
      active = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const navigate = (next, payload) => {
    let clearedProfile = false
    if (payload !== undefined) {
      applyAnswers(payload)
      if (payload === null) {
        // start over: drop the saved profile so the next run creates a fresh one
        setProfileId(null)
        try {
          localStorage.removeItem(PROFILE_KEY)
        } catch {
          /* ignore */
        }
        clearedProfile = true
      } else {
        // persist completed/edited answers (fire-and-forget; UI proceeds regardless)
        saveProfile(payload).catch(() => {})
      }
    }

    // Returning visitors re-entering the quiz land on their editable profile instead.
    // Safe to read profileId from the closure here: the only async setProfileId (in saveProfile)
    // happens on a 'recommendations'/save navigation, which always precedes any later
    // 'questionnaire' re-entry by a full navigation; and a same-call start-over is covered
    // by clearedProfile.
    let target = next
    if (target === 'questionnaire' && profileId && !clearedProfile) target = 'profile'

    const path = PATHS[target] || '/'
    if (window.location.pathname !== path) {
      window.history.pushState({}, '', path)
    }
    setView(target)
    window.scrollTo(0, 0)
  }

  // Recommendations and profile need answers; without any (and no saved profile to
  // hydrate from), send the user to the quiz.
  useEffect(() => {
    if ((view === 'recommendations' || view === 'profile') && !answers && !profileId) {
      navigate('questionnaire')
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [view, answers, profileId])

  if (view === 'questionnaire') {
    return <QuestionnairePage onNavigate={navigate} />
  }
  if (view === 'recommendations' || view === 'profile') {
    if (!answers) {
      if (hydrationError) {
        return (
          <main className="recs">
            <div className="recs__state">Couldn't load your saved preferences.</div>
            <div className="recs__actions">
              <button className="btn-primary" type="button" onClick={retryHydration}>Try Again</button>
              <button className="quiz__restart" type="button" onClick={() => navigate('questionnaire', null)}>Start Fresh</button>
            </div>
          </main>
        )
      }
      return null // hydrating / redirecting
    }
    return view === 'recommendations'
      ? <RecommendationsPage answers={answers} onNavigate={navigate} />
      : <ProfilePage answers={answers} onNavigate={navigate} onSaveProfile={handleSaveProfile} />
  }
  return <LandingPage onNavigate={navigate} />
}
