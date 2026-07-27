import { test } from 'node:test'
import assert from 'node:assert/strict'
import { QUESTIONS } from './questions.js'
import { colourToHex } from '../colours.js'

// The brands the catalogue stocks, spelled exactly as mouse_model.brand_name spells
// them. If a scraper adds a seventh brand, this list and Q18 both need updating —
// that's the point of pinning it here rather than trusting the two to agree.
const CATALOGUE_BRANDS = ['Logitech', 'Asus', 'Razer', 'HP', 'UGreen', 'HyperX']

const chooseable = (id) => QUESTIONS[id].options.map((o) => o.value).filter((v) => v !== 'none')

test('every brand offered is spelled like a real brand_name', () => {
  // The catalogue's brand filter compares an option's value against brand_name
  // directly, so a typo here matches nothing and fails silently.
  for (const value of chooseable(18)) {
    assert.ok(CATALOGUE_BRANDS.includes(value), `"${value}" is not a brand in the catalogue`)
  }
})

test('no catalogue brand is left out of the quiz', () => {
  const offered = chooseable(18)
  for (const brand of CATALOGUE_BRANDS) {
    assert.ok(offered.includes(brand), `${brand} has mice but the quiz never offers it`)
  }
})

test('the exclusive "No Preference" brand option is still exclusive', () => {
  const none = QUESTIONS[18].options.find((o) => o.value === 'none')
  assert.equal(none.exclusive, true)
})

test('every colour offered is one colourToHex can resolve', () => {
  // An option colourToHex doesn't recognise would be a colour the user can ask for
  // but which renders as the neutral "unknown" swatch everywhere else.
  for (const value of chooseable(21)) {
    assert.notEqual(colourToHex(value), null, `"${value}" resolves to no swatch colour`)
  }
})

test('the original colour values survive so saved answers still match', () => {
  // Profiles created before the list grew stored these; changing the strings would
  // leave those answers matching no option, and the profile page would show the
  // question as unanswered.
  for (const value of ['Black', 'White', 'Pink']) {
    assert.ok(chooseable(21).includes(value), `${value} was dropped or renamed`)
  }
})

test('each colour family is distinct — no two options mean the same swatch', () => {
  const hexes = chooseable(21).map(colourToHex)
  assert.equal(new Set(hexes).size, hexes.length, 'two colour options map to one family')
})
