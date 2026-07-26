import { User, Grid, Sparkle } from './icons.jsx'

const PROFILE_KEY = 'pickwise_profile_id'

// Which icon owns which view. The questionnaire is the first-run form of the
// profile — App redirects between the two depending on whether one is saved — so
// they light the same icon. Product and compare pages deliberately map to
// nothing: they aren't any of these three destinations, and guessing a section
// for them would light an icon that doesn't take you back where you came from.
const ICON_FOR_VIEW = {
  landing: 'catalogue',
  recommendations: 'recommendations',
  profile: 'profile',
  questionnaire: 'profile',
}

export default function Navbar({ onNavigate, view }) {
  const current = ICON_FOR_VIEW[view] || null

  // Marks the icon for the page being viewed. aria-current is what actually
  // conveys this to a screen reader — the gradient is only visual.
  const mark = (key) => ({
    className: 'navbar__icon-btn' + (current === key ? ' is-current' : ''),
    'aria-current': current === key ? 'page' : undefined,
  })

  const go = (view) => (e) => {
    if (onNavigate) {
      e.preventDefault()
      onNavigate(view)
    }
  }

  // The profile icon opens the saved profile when one exists; otherwise it starts
  // the questionnaire (which itself redirects to the profile if one is found).
  const openProfile = (e) => {
    e.preventDefault()
    let hasProfile = false
    try {
      hasProfile = !!localStorage.getItem(PROFILE_KEY)
    } catch {
      /* ignore */
    }
    if (onNavigate) onNavigate(hasProfile ? 'profile' : 'questionnaire')
  }

  return (
    <header className="navbar">
      <a className="navbar__brand" href="/" onClick={go('landing')}>
        <img className="navbar__logo" src="/logo.png" alt="PickWise logo" />
        PickWise
      </a>
      <nav className="navbar__nav">
        {/* Icon first, label after it, so the expanded pill reads icon-then-text.
            The button's right edge is pinned by the nav being right-anchored, so
            the growth comes out of the left side and the icon travels with it.
            No `title` on these any more: it would fire a native tooltip on top of
            the label that's already appearing. The label text is the accessible
            name — it stays in the accessibility tree while collapsed, because
            it's hidden by overflow rather than by `display: none`. */}
        <button
          {...mark('recommendations')}
          type="button"
          onClick={go('recommendations')}
          aria-label="For You — personalised recommendations"
        >
          <Sparkle />
          <span className="navbar__label">For You</span>
        </button>
        <a {...mark('catalogue')} href="/catalogue" onClick={go('landing')}>
          <Grid />
          <span className="navbar__label">Catalogue</span>
        </a>
        <button {...mark('profile')} type="button" onClick={openProfile}>
          <User />
          <span className="navbar__label">Profile</span>
        </button>
      </nav>
    </header>
  )
}
