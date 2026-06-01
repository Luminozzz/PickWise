import { User, Grid } from './icons.jsx'

export default function Navbar() {
  return (
    <header className="navbar">
      <a className="navbar__brand" href="/">
        <img className="navbar__logo" src="/logo.png" alt="PickWise logo" />
        PickWise
      </a>
      <nav className="navbar__nav">
        <a
          className="navbar__icon-btn"
          href="/catalogue"
          aria-label="Catalogue"
          title="Catalogue"
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