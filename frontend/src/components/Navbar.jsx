import { User, Grid, Sparkle } from './icons.jsx'

const PROFILE_KEY = 'pickwise_profile_id'

export default function Navbar({ onNavigate }) {
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
        <button
          className="navbar__icon-btn"
          type="button"
          onClick={go('questionnaire')}
          aria-label="Find my mouse with AI"
          title="Find my mouse"
        >
          <Sparkle />
        </button>
        <a
          className="navbar__icon-btn"
          href="/catalogue"
          aria-label="Catalogue"
          title="Catalogue"
          onClick={go('landing')}
        >
          <Grid />
        </a>
        <button
          className="navbar__icon-btn navbar__icon-btn--profile"
          type="button"
          onClick={openProfile}
          aria-label="Profile"
          title="Profile"
        >
          <User />
        </button>
      </nav>
    </header>
  )
}
