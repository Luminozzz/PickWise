// The product categories the landing page offers.
//
// `ready` is what makes a category real: mice have a catalogue, a questionnaire and
// a ranking algorithm behind them, and the other three have nothing yet. Rather
// than hide them, they lead to a page that says so — the roadmap is worth showing,
// and a category that vanishes until it ships tells a visitor nothing.
//
// Adding a category here puts a card on the landing page. Flipping `ready` to true
// is not enough to launch one: it needs a route, which routes.js resolves by slug.
export const CATEGORIES = [
  {
    slug: 'mouse',
    title: 'Mouse',
    tagline: 'Find your grip, weight and sensor',
    ready: true,
  },
  {
    slug: 'keyboard',
    title: 'Keyboard',
    tagline: 'Switches, layout and feel',
    ready: false,
  },
  {
    slug: 'monitor',
    title: 'Monitor',
    tagline: 'Size, refresh rate and panel',
    ready: false,
  },
  {
    slug: 'laptop',
    title: 'Laptop',
    tagline: 'Power, portability and battery',
    ready: false,
  },
]

export const categoryBySlug = (slug) => CATEGORIES.find((c) => c.slug === slug) || null
