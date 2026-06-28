import { useState } from 'react'
import { QUESTIONS } from './questions.js'
import { INITIAL_STACK, computeNext, currentId, remainingCount } from './engine.js'

// Drives the questionnaire: current question, answers, progress, back/restart.
export function useQuestionnaire() {
  const [state, setState] = useState({
    stack: INITIAL_STACK,
    answers: {},
    history: [], // snapshots of { stack, answers } for the Back button
    direction: 1, // 1 = forward, -1 = back (for slide animation)
  })

  const id = currentId(state.stack)
  const question = id != null ? QUESTIONS[id] : null
  const done = id == null

  const stepNumber = state.history.length + 1
  const remaining = remainingCount(state.stack) // includes the current question
  const progress = done
    ? 1
    : state.history.length / (state.history.length + remaining)

  function advance(jump, value) {
    setState((prev) => {
      const curId = currentId(prev.stack)
      const answers =
        value === undefined ? prev.answers : { ...prev.answers, [curId]: value }
      return {
        stack: computeNext(prev.stack, jump),
        answers,
        // snapshot the post-answer `answers` so Back restores the value the
        // user gave for the question they return to (and re-shows its selection)
        history: [...prev.history, { stack: prev.stack, answers }],
        direction: 1,
      }
    })
  }

  // A select option: record its value and apply any jump it carries.
  function select(option) {
    advance(
      { enter: option.enter, goto: option.goto, push: option.push },
      option.value,
    )
  }

  // A slider/range/multiselect value: record and advance with no jump.
  function submit(value) {
    advance(null, value)
  }

  function back() {
    setState((prev) => {
      if (!prev.history.length) return prev
      const last = prev.history[prev.history.length - 1]
      return {
        stack: last.stack,
        answers: last.answers,
        history: prev.history.slice(0, -1),
        direction: -1,
      }
    })
  }

  function restart() {
    setState({ stack: INITIAL_STACK, answers: {}, history: [], direction: 1 })
  }

  return {
    question,
    answers: state.answers,
    done,
    stepNumber,
    progress,
    direction: state.direction,
    canBack: state.history.length > 0,
    select,
    submit,
    back,
    restart,
  }
}
