import { User, Grid, Sparkle } from './icons.jsx'

export default function Navbar({ onNavigate }) {
  const go = (view) => (e) => {
    if (onNavigate) {
      e.preventDefault()
      onNavigate(view)
    }
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
          aria-label="Login"
          title="Login"
        >
          <User />
        </button>
      </nav>
    </header>
  )
}