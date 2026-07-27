import Navbar from '../components/Navbar.jsx'
import { CATEGORY_ICON } from '../components/icons.jsx'
import { CATEGORIES } from '../categories.js'
import { pathForCategory } from '../routes.js'

// The front door. The wordmark holds the middle of the first screen on its own,
// then the categories sit below it, so the page says what this is before it asks
// you to pick something.
export default function HomePage({ onNavigate }) {
  // Real hrefs, intercepted: middle-click and open-in-new-tab keep working, and the
  // status bar shows where a card goes before you commit to it.
  const go = (category) => (e) => {
    if (!onNavigate) return
    e.preventDefault()
    if (category.ready) onNavigate('catalogue')
    else onNavigate('soon', category.slug)
  }

  return (
    <>
      <Navbar onNavigate={onNavigate} view="home" />
      <div className="sky" aria-hidden="true">
        <span className="sky__stars" />
        <span className="sky__stars sky__stars--far" />
      </div>

      <main className="home">
        <section className="home__hero">
          <h1 className="home__wordmark">PickWise</h1>
          <p className="home__tagline">Finding your perfect fit has never been this easy.</p>
        </section>

        <section className="home__categories">
          <h2 className="home__eyebrow">Choose a Category</h2>
          <ul className="home__grid">
            {CATEGORIES.map((category, i) => {
              const Icon = CATEGORY_ICON[category.slug]
              return (
                <li className="home__grid-item" key={category.slug} style={{ '--card-index': i }}>
                  <a
                    className={'catcard' + (category.ready ? '' : ' catcard--soon')}
                    href={pathForCategory(category)}
                    onClick={go(category)}
                  >
                    <span className="catcard__art">{Icon ? <Icon size={56} /> : null}</span>
                    <span className="catcard__title">{category.title}</span>
                    <span className="catcard__tagline">{category.tagline}</span>
                    {/* Says so up front rather than after the click. The card still
                        goes somewhere — the roadmap is worth showing — but nobody
                        should have to open it to find out it isn't built. */}
                    {!category.ready && <span className="catcard__badge">Soon</span>}
                  </a>
                </li>
              )
            })}
          </ul>
        </section>
      </main>
    </>
  )
}
