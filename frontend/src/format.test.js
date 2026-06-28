import { test } from 'node:test'
import assert from 'node:assert/strict'
import { formatCount } from './format.js'

test('counts under 1000 stay a plain number', () => {
  assert.equal(formatCount(0), '0')
  assert.equal(formatCount(950), '950')
  assert.equal(formatCount(999), '999')
})

test('1000+ abbreviates to "k" (one decimal, trailing .0 dropped)', () => {
  assert.equal(formatCount(1000), '1k')
  assert.equal(formatCount(1500), '1.5k')
  assert.equal(formatCount(1234), '1.2k')
  assert.equal(formatCount(1999), '2k')
  assert.equal(formatCount(12000), '12k')
  assert.equal(formatCount(12345), '12.3k')
})

test('nullish / non-finite returns null', () => {
  assert.equal(formatCount(null), null)
  assert.equal(formatCount(undefined), null)
  assert.equal(formatCount(NaN), null)
})
