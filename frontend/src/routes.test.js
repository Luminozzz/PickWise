import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  PATHS,
  viewForPath,
  productIdFromPath,
  compareIdsFromPath,
  categoryFromPath,
  pathForCategory,
} from './routes.js'
import { CATEGORIES, categoryBySlug } from './categories.js'

test('the root path is the landing page, not the catalogue', () => {
  // This is the change the landing page made: / used to fall through to the
  // catalogue via the catch-all, and every "back to catalogue" button relied on it.
  assert.equal(viewForPath('/'), 'home')
  assert.equal(viewForPath('/catalogue'), 'catalogue')
})

test('every path in PATHS resolves back to the view it belongs to', () => {
  // PATHS and viewForPath are inverses. If they disagree, navigate() pushes a URL
  // that a reload or a back button reads as a different screen.
  for (const [view, path] of Object.entries(PATHS)) {
    assert.equal(viewForPath(path), view, `${path} does not map back to "${view}"`)
  }
})

test('a trailing slash is the same page', () => {
  assert.equal(viewForPath('/catalogue/'), 'catalogue')
  assert.equal(viewForPath('/profile/'), 'profile')
  assert.equal(viewForPath('/soon/keyboard/'), 'soon')
})

test('an unrecognised path lands on the landing page', () => {
  for (const path of ['/nope', '/catalog', '/soon', '/mouse', '']) {
    assert.equal(viewForPath(path), 'home', `${path} should fall back to home`)
  }
})

test('product and compare paths still resolve', () => {
  assert.equal(viewForPath('/product/42'), 'product')
  assert.equal(productIdFromPath('/product/42'), 42)
  assert.equal(viewForPath('/compare'), 'compare')
  assert.equal(viewForPath('/compare/1-2-3'), 'compare')
  assert.deepEqual(compareIdsFromPath('/compare/1-2-3'), [1, 2, 3])
})

// ---- categories -------------------------------------------------------------- //

test('every unbuilt category has a reachable coming soon page', () => {
  for (const category of CATEGORIES.filter((c) => !c.ready)) {
    const path = pathForCategory(category)
    assert.equal(viewForPath(path), 'soon', `${category.slug} has no coming soon route`)
    assert.equal(categoryFromPath(path), category.slug)
  }
})

test('a built category has no coming soon page', () => {
  // /soon/mouse would render a page saying mice aren't built, next to a catalogue
  // full of them.
  for (const category of CATEGORIES.filter((c) => c.ready)) {
    assert.equal(categoryFromPath(`/soon/${category.slug}`), null)
    assert.equal(viewForPath(`/soon/${category.slug}`), 'home')
  }
})

test('a card for a built category points at something built', () => {
  for (const category of CATEGORIES.filter((c) => c.ready)) {
    assert.notEqual(viewForPath(pathForCategory(category)), 'soon')
    assert.notEqual(viewForPath(pathForCategory(category)), 'home')
  }
})

test('an unknown category slug is not a coming soon page', () => {
  for (const path of ['/soon/webcam', '/soon/', '/soon/MOUSE', '/soon/key-board']) {
    assert.equal(categoryFromPath(path), null, `${path} resolved to a category`)
  }
})

test('the categories the landing page promises are the four asked for', () => {
  assert.deepEqual(
    CATEGORIES.map((c) => c.slug),
    ['mouse', 'keyboard', 'monitor', 'laptop'],
  )
  // Mice are the only category with an algorithm behind them today.
  assert.deepEqual(CATEGORIES.filter((c) => c.ready).map((c) => c.slug), ['mouse'])
})

test('every category has a title and a tagline to put on its card', () => {
  for (const c of CATEGORIES) {
    assert.ok(c.title?.length, `${c.slug} has no title`)
    assert.ok(c.tagline?.length, `${c.slug} has no tagline`)
    assert.equal(categoryBySlug(c.slug), c)
  }
})

test('categoryBySlug does not invent categories', () => {
  assert.equal(categoryBySlug('webcam'), null)
  assert.equal(categoryBySlug(undefined), null)
})
