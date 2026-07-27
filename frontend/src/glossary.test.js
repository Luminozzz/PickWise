import { test } from 'node:test'
import assert from 'node:assert/strict'
import { TERMS, SPEC_HELP } from './glossary.js'
import { QUESTIONS } from './questionnaire/questions.js'

// The spec rows the backend emits, keyed as _SPECS in algorithm/recommend.py spells
// them. The product page and the compare table are both built from that list, so a
// key added there with nothing added here means a spec row with no explanation.
// Pinning the list is the point: the frontend can't see the backend at test time.
const SPEC_KEYS = [
  'weight',
  'max_DPI',
  'polling',
  'tracking',
  'buttons',
  'connectivity',
  'battery',
  'size',
  'ergonomy',
  'rgb',
  'left',
  'price',
]

test('every spec row the backend sends has an explanation', () => {
  for (const key of SPEC_KEYS) {
    assert.ok(SPEC_HELP[key], `spec "${key}" is shown with no help`)
  }
})

test('no explanation is keyed to a spec that does not exist', () => {
  // A stale key is dead copy: it never renders, so nobody notices it went wrong.
  for (const key of Object.keys(SPEC_HELP)) {
    assert.ok(SPEC_KEYS.includes(key), `"${key}" matches no spec row`)
  }
})

test('every glossary entry has a term to bold and real text', () => {
  for (const [id, entry] of Object.entries(TERMS)) {
    assert.ok(entry.term?.length, `TERMS.${id} has no term`)
    assert.ok(entry.text?.length > 40, `TERMS.${id} has no real explanation`)
  }
})

test('each spec row is explained under the term it should be', () => {
  // The panel bolds entry.term above the text, so a wrong pairing reads as if the
  // panel is explaining some other spec. Two deliberately differ from the row's own
  // label: "Max DPI" is explained as DPI and "RGB lighting" as RGB, because the term
  // being defined is narrower than the label the row happens to use.
  const TERM_FOR_KEY = {
    weight: 'Weight',
    max_DPI: 'DPI',
    polling: 'Polling rate',
    tracking: 'Tracking speed',
    buttons: 'Buttons',
    connectivity: 'Connectivity',
    battery: 'Battery life',
    size: 'Dimensions',
    ergonomy: 'Shape',
    rgb: 'RGB',
    left: 'Left-handed use',
    price: 'Price',
  }
  for (const [key, term] of Object.entries(TERM_FOR_KEY)) {
    assert.equal(SPEC_HELP[key].term, term, `spec "${key}" is explained under the wrong name`)
  }
})

test('the terms the quiz and the specs share are one definition, not two copies', () => {
  // Identity, not equality: equal strings would pass while still being two copies
  // that can drift. These five are asked about in the quiz and shown as a spec.
  const SHARED = [
    [SPEC_HELP.max_DPI, TERMS.dpi, 20],
    [SPEC_HELP.polling, TERMS.polling, 20],
    [SPEC_HELP.rgb, TERMS.rgb, 7],
    [SPEC_HELP.weight, TERMS.weight, 6],
    [SPEC_HELP.connectivity, TERMS.connectivity, 15],
  ]
  for (const [spec, term, questionId] of SHARED) {
    assert.equal(spec, term, `${term.term} is not the same entry in both places`)
    assert.ok(
      QUESTIONS[questionId].help.includes(term),
      `Q${questionId} no longer uses the shared ${term.term} entry`,
    )
  }
})

test('no two terms are explained with the same words', () => {
  // Two entries with identical text means one was copied and the other forgotten.
  const texts = Object.values(TERMS).map((e) => e.text)
  assert.equal(new Set(texts).size, texts.length, 'two glossary entries share their text')
})

test('the quiz only ever references entries that exist', () => {
  // help: [TERMS.typo] is undefined, and InfoButton renders nothing for it, so a
  // misspelt reference silently drops the explanation instead of erroring.
  const entries = new Set(Object.values(TERMS))
  for (const q of Object.values(QUESTIONS)) {
    for (const entry of q.help || []) {
      assert.ok(entry && entries.has(entry), `Q${q.id} references a term that is not in TERMS`)
    }
    for (const opt of q.options || []) {
      if (opt.help) {
        assert.ok(entries.has(opt.help), `Q${q.id}/${opt.value} references a missing term`)
      }
    }
  }
})
