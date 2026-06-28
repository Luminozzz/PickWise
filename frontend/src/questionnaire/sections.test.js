import { test } from 'node:test'
import assert from 'node:assert/strict'
import { profileSections } from './sections.js'

test('gamer persona then about', () => {
  const s = profileSections({ 1: 'gamer' })
  assert.deepEqual(s.map((x) => x.key), ['gamer', 'about'])
  assert.deepEqual(s[0].questionIds, [5, 6, 7, 8, 19, 20])
})

test('student who games reveals the gamer block', () => {
  const base = profileSections({ 1: 'student' })[0].questionIds
  assert.deepEqual(base, [2, 3, 4])
  const gaming = profileSections({ 1: 'student', 2: 'regularly' })[0].questionIds
  assert.deepEqual(gaming, [2, 3, 4, 5, 6, 7, 8, 19, 20])
})

test('wired-too (16) only when wireless is yes/preferably', () => {
  const about = (a) => profileSections(a).find((x) => x.key === 'about').questionIds
  assert.ok(!about({ 1: 'office' }).includes(16))
  assert.ok(about({ 1: 'office', 15: 'yes' }).includes(16))
  assert.ok(about({ 1: 'office', 15: 'preferably' }).includes(16))
  assert.ok(!about({ 1: 'office', 15: 'no' }).includes(16))
  // 16 sits immediately after 15
  const ids = about({ 1: 'office', 15: 'yes' })
  assert.equal(ids[ids.indexOf(15) + 1], 16)
})

test('no persona section when user type is unset', () => {
  const s = profileSections({})
  assert.deepEqual(s.map((x) => x.key), ['about'])
})
