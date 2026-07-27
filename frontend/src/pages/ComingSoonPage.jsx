import Navbar from '../components/Navbar.jsx'
import { CATEGORY_ICON, ArrowRight } from '../components/icons.jsx'
import { categoryBySlug } from '../categories.js'

// Where an unbuilt category lands. Deliberately thin: it says which category, that
// it isn't ready, and offers the one that is, rather than pretending to be a
// product page with nothing behind it.
export default function ComingSoonPage({ category: slug, onNavigate }) {
  const category = categoryBySlug(slug)
  const Icon = category ? CATEGORY_ICON[category.slug] : null
  const name = category ? category.title.toLowerCase() : 'this category'

  return (
    <>
      <Navbar onNavigate={onNavigate} view="soon" />
      <div className="sky" aria-hidden="true">
        <span className="sky__stars" />
      </div>

      <main className="soon">
        <span className="soon__art">{Icon ? <Icon size={72} /> : null}</span>
        <span className="soon__badge">Coming Soon</span>
        <h1 className="soon__title">{category ? category.title : 'Coming Soon'}</h1>
        <p className="soon__body">
          We're still gathering {name} data and tuning the questions that rank it. Mice
          are ready today, and the rest follow the same way: real specs, real prices,
          ranked against what you actually need.
        </p>
        <div className="soon__actions">
          <button className="btn-primary" type="button" onClick={() => onNavigate('catalogue')}>
            Browse mice <ArrowRight size={14} />
          </button>
          <button className="quiz__restart" type="button" onClick={() => onNavigate('home')}>
            All categories
          </button>
        </div>
      </main>
    </>
  )
}
