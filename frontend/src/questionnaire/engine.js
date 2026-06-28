// Stack-based traversal for a branching questionnaire with "jump and return".
//
// The stack holds frames (arrays of question ids). The current question is the
// first id of the top-most non-empty frame; advancing consumes it. An option
// can push sub-flows on top of the stack — those run to completion, then the
// engine returns to the frame underneath. This gives call/return semantics:
//
//   answer Q2 with goto:5  ->  push [5,6,7,8] on top of remaining [3,4]
//   run 5,6,7,8, frame empties, pop  ->  resume [3,4]

import { FLOWS } from './questions.js'

// Trim trailing (top-most) empty frames so the top frame always has a question.
export function dropEmpty(stack) {
  const s = stack.map((f) => f.slice())
  while (s.length && s[s.length - 1].length === 0) s.pop()
  return s
}

// The id of the question to show next, or null when finished.
export function currentId(stack) {
  const s = dropEmpty(stack)
  return s.length ? s[s.length - 1][0] : null
}

// How many questions remain on the stack, including the current one.
export function remainingCount(stack) {
  return stack.reduce((total, frame) => total + frame.length, 0)
}

// The slice of a flow from `qid` to the end of whichever flow contains it.
export function flowSliceFrom(qid) {
  for (const ids of Object.values(FLOWS)) {
    const i = ids.indexOf(qid)
    if (i !== -1) return ids.slice(i)
  }
  return [qid]
}

// Produce the next stack after answering the current question.
// `jump` (optional): { enter?: flowId[], goto?: qid, push?: qid[] }.
export function computeNext(stack, jump) {
  const s = dropEmpty(stack)

  // Consume the current question from the top frame.
  if (s.length) s[s.length - 1] = s[s.length - 1].slice(1)

  if (jump) {
    // enter: push whole named flows in order (last ends up on top / runs first)
    if (jump.enter) for (const flowId of jump.enter) s.push(FLOWS[flowId].slice())
    // goto: jump into another flow at a specific question, run to its end
    if (jump.goto != null) s.push(flowSliceFrom(jump.goto))
    // push: an explicit ad-hoc sub-flow (e.g. a conditional follow-up question)
    if (jump.push) s.push(jump.push.slice())
  }

  return dropEmpty(s)
}

export const INITIAL_STACK = [[1]]
