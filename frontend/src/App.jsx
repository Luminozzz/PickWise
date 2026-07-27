import { useState, useEffect } from 'react'
import HomePage from './pages/HomePage.jsx'
import CataloguePage from './pages/CataloguePage.jsx'
import ComingSoonPage from './pages/ComingSoonPage.jsx'
import QuestionnairePage from './pages/QuestionnairePage.jsx'
import RecommendationsPage from './pages/RecommendationsPage.jsx'
import ProfilePage from './pages/ProfilePage.jsx'
import ProductPage from './pages/ProductPage.jsx'
import ComparePage from './pages/ComparePage.jsx'
import { createProfile, getProfile, updateProfile } from './api.js'
import {
  PATHS,
  viewForPath,
  productIdFromPath,
  compareIdsFromPath,
  categoryFromPath,
  hasRealAnswers,
  redirectForMissingAnswers,
} from './routes.js'

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
  const [category, setCategory] = useState(() => categoryFromPath(window.location.pathname))
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
      setCategory(categoryFromPath(path))
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

  const navigate = (next, payload, { replace = false } = {}) => {
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

    // Coming soon: the payload is a category slug. Like the two above, this must
    // return before the block below, which would otherwise adopt the slug as the
    // user's answers and PUT it to their saved profile.
    if (next === 'soon') {
      setCategory(payload)
      const soonPath = `/soon/${payload}`
      if (window.location.pathname !== soonPath) {
        window.history.pushState({}, '', soonPath)
      }
      setView('soon')
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

    // "For You" and the profile page need answers to be about anything, so the quiz
    // takes their place when there are none. Decided here rather than only in the
    // effect below so the click goes straight to the quiz: redirecting after the
    // fact flashes a page of unranked mice and leaves a /recommendations entry in
    // the history that bounces straight back here.
    //
    // The payload is the truth when one was passed — applyAnswers above is a
    // setState, so the closure's `answers` is still the previous value, and reading
    // it would send someone back to the quiz the moment they finished it.
    const answersNow = payload !== undefined ? payload : answers
    const stand = redirectForMissingAnswers(target, {
      hasAnswers: hasRealAnswers(answersNow),
      hasProfile: !!profileId && !clearedProfile,
    })
    if (stand) target = stand

    const path = PATHS[target] || '/'
    if (window.location.pathname !== path) {
      if (replace) window.history.replaceState({}, '', path)
      else window.history.pushState({}, '', path)
    }
    setView(target)
    window.scrollTo(0, 0)
  }

  // Covers arriving cold on one of those URLs — a bookmark, a shared link, a
  // reload — which the check inside navigate() never sees. Replaces rather than
  // pushes: the URL being left redirects here again, so pushing would trap the back
  // button bouncing between the two.
  useEffect(() => {
    const stand = redirectForMissingAnswers(view, {
      hasAnswers: hasRealAnswers(answers),
      hasProfile: !!profileId,
    })
    if (stand) navigate(stand, undefined, { replace: true })
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
    if (!answers && profileId) return hydrationFallback()
    // No answers and no profile: the effect above is sending this to the quiz. Render
    // nothing for that one frame rather than a page of mice ranked against nothing.
    if (!hasRealAnswers(answers)) return null
    return <RecommendationsPage answers={answers} onNavigate={navigate} />
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
  if (view === 'catalogue') {
    return <CataloguePage onNavigate={navigate} answers={answers} />
  }
  if (view === 'soon') {
    return <ComingSoonPage category={category} onNavigate={navigate} />
  }
  return <HomePage onNavigate={navigate} />
}
