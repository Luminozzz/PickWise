import { useState, useEffect } from 'react'
import LandingPage from './pages/LandingPage.jsx'
import QuestionnairePage from './pages/QuestionnairePage.jsx'
import RecommendationsPage from './pages/RecommendationsPage.jsx'
import ProfilePage from './pages/ProfilePage.jsx'
import ProductPage from './pages/ProductPage.jsx'
import ComparePage from './pages/ComparePage.jsx'
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
  if (path.startsWith('/product/')) return 'product'
  if (path === '/compare' || path.startsWith('/compare/')) return 'compare'
  return 'landing'
}

function productIdFromPath(path) {
  const match = (path || '').match(/^\/product\/(\d+)/)
  return match ? Number(match[1]) : null
}

// The compared mouse ids live in the URL (/compare/1-2-3), left to right. Bad or
// repeated ids are dropped rather than rejected, so a hand-typed link still
// renders. No cap here: how many columns fit is the view's call, not the URL's.
function compareIdsFromPath(path) {
  // Digits joined by single dashes, nothing else: a looser pattern lets
  // /compare/-1 through, where the empty leading segment becomes 0 and the "1"
  // silently renders mouse #1.
  const match = (path || '').match(/^\/compare\/(\d+(?:-\d+)*)\/?$/)
  if (!match) return []
  const ids = []
  for (const part of match[1].split('-')) {
    const n = Number(part)
    if (Number.isInteger(n) && n > 0 && !ids.includes(n)) ids.push(n)
  }
  return ids
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
  const [productId, setProductId] = useState(() => productIdFromPath(window.location.pathname))
  const [compareIds, setCompareIds] = useState(() => compareIdsFromPath(window.location.pathname))
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
    const onPop = () => {
      const path = window.location.pathname
      setView(viewForPath(path))
      setProductId(productIdFromPath(path))
      setCompareIds(compareIdsFromPath(path))
    }
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
    // Product detail: the payload is the mouse id, not answers.
    if (next === 'product') {
      setProductId(payload)
      const productPath = `/product/${payload}`
      if (window.location.pathname !== productPath) {
        window.history.pushState({}, '', productPath)
      }
      setView('product')
      window.scrollTo(0, 0)
      return
    }

    // Compare: the payload is a list of mouse ids, not answers. This must return
    // before the block below, which would otherwise adopt the array as the
    // user's answers and PUT it to their saved profile (silently — saveProfile
    // swallows its rejection).
    if (next === 'compare') {
      const ids = []
      for (const value of Array.isArray(payload) ? payload : [payload]) {
        const n = Number(value)
        if (Number.isInteger(n) && n > 0 && !ids.includes(n)) ids.push(n)
      }
      setCompareIds(ids)
      const comparePath = ids.length ? `/compare/${ids.join('-')}` : '/compare'
      if (window.location.pathname !== comparePath) {
        window.history.pushState({}, '', comparePath)
      }
      setView('compare')
      window.scrollTo(0, 0)
      return
    }

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

  // Editing a profile needs answers; without any (and no saved profile to hydrate
  // from), send the user to the quiz. Recommendations don't require a profile —
  // with none they fall back to general (public) ranking.
  useEffect(() => {
    if (view === 'profile' && !answers && !profileId) {
      navigate('questionnaire')
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [view, answers, profileId])

  const hydrationFallback = () => {
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
    return null // hydrating
  }

  if (view === 'questionnaire') {
    return <QuestionnairePage onNavigate={navigate} />
  }
  if (view === 'recommendations') {
    // With a saved profile we wait for hydration; with none, show general results.
    if (!answers && profileId) return hydrationFallback()
    return <RecommendationsPage answers={answers || {}} onNavigate={navigate} />
  }
  if (view === 'profile') {
    if (!answers) return hydrationFallback()
    return <ProfilePage answers={answers} onNavigate={navigate} onSaveProfile={handleSaveProfile} />
  }
  if (view === 'product') {
    return <ProductPage productId={productId} answers={answers} onNavigate={navigate} />
  }
  if (view === 'compare') {
    // Row order is this page's whole point, so wait for a saved profile rather
    // than flashing default-ordered rows and reshuffling once it hydrates.
    if (!answers && profileId) return hydrationFallback()
    return <ComparePage productIds={compareIds} answers={answers} onNavigate={navigate} />
  }
  return <LandingPage onNavigate={navigate} answers={answers} />
}
