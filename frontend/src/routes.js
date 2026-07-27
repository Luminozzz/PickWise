// Path <-> view mapping, kept out of App.jsx so it can be tested: the test runner
// is plain `node --test`, which has no JSX loader.
//
// There is no router. A view name is the app's internal id for a screen, PATHS is
// the URL it lives at, and viewForPath is the inverse for a cold load or a back
// button. Views not in PATHS carry state in the URL (a product id, compared ids, a
// category slug) and are pushed by App's navigate() instead.
import { categoryBySlug } from './categories.js'

export const PATHS = {
  home: '/',
  catalogue: '/catalogue',
  questionnaire: '/questionnaire',
  recommendations: '/recommendations',
  profile: '/profile',
}

// A trailing slash is the same page. Without this, /catalogue/ falls through to the
// catch-all and silently lands on the home page instead.
const normalise = (path) => (path && path !== '/' ? path.replace(/\/+$/, '') || '/' : '/')

export function viewForPath(path) {
  const p = normalise(path)
  if (p === '/') return 'home'
  if (p === '/catalogue') return 'catalogue'
  if (p === '/questionnaire') return 'questionnaire'
  if (p === '/recommendations') return 'recommendations'
  if (p === '/profile') return 'profile'
  if (p.startsWith('/product/')) return 'product'
  if (p === '/compare' || p.startsWith('/compare/')) return 'compare'
  if (categoryFromPath(p)) return 'soon'
  // Anything unrecognised lands on the home page: it names the whole product and
  // every category is one click from it, which a bare catalogue can't say.
  return 'home'
}

export function productIdFromPath(path) {
  const match = (path || '').match(/^\/product\/(\d+)/)
  return match ? Number(match[1]) : null
}

// The compared mouse ids live in the URL (/compare/1-2-3), left to right. Bad or
// repeated ids are dropped rather than rejected, so a hand-typed link still
// renders. No cap here: how many columns fit is the view's call, not the URL's.
export function compareIdsFromPath(path) {
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

// Which unbuilt category /soon/<slug> is about. A slug that names no category, or
// one that is already built, resolves to null so viewForPath falls through to the
// home page: there is no "coming soon" for something that has shipped, and
// /soon/mouse would otherwise render a page contradicting the catalogue.
export function categoryFromPath(path) {
  const match = normalise(path).match(/^\/soon\/([a-z]+)$/)
  if (!match) return null
  const category = categoryBySlug(match[1])
  return category && !category.ready ? category.slug : null
}

// An empty object is not a set of answers. It is truthy, so a plain falsy check
// lets it through, and a profile can exist with nothing filled in.
export const hasRealAnswers = (answers) =>
  !!answers && Object.keys(answers).length > 0

// The views that only mean something once there are answers behind them: "For You"
// ranks mice around them, and the profile page edits them. Shown with none, the
// first ranks against nothing and reports 0 matched on every row, and the second is
// a blank form — so the quiz stands in, because it is what the visitor needs to get
// either one working.
//
// A saved profile counts even before its answers arrive: they are being fetched, and
// redirecting mid-flight would throw a returning visitor into a quiz they already
// finished.
//
// Returns the view to show instead, or null to show the one that was asked for.
const NEEDS_ANSWERS = ['recommendations', 'profile']

export function redirectForMissingAnswers(view, { hasAnswers, hasProfile }) {
  if (hasAnswers || hasProfile) return null
  return NEEDS_ANSWERS.includes(view) ? 'questionnaire' : null
}

// Where a category card points.
export function pathForCategory(category) {
  if (!category) return PATHS.home
  if (!category.ready) return `/soon/${category.slug}`
  // Mice are the only built category, and the catalogue, questionnaire, rankings
  // and compare table are all mouse specific, so the mouse card goes to
  // /catalogue rather than /catalogue/mouse. A second ready category would need
  // those routes namespaced by category first — this returns the same path for
  // every ready category, which is correct only while there is one.
  return PATHS.catalogue
}
