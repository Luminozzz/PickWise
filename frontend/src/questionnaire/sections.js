// Pure selector: given the answers, return the ordered, grouped questions the
// profile page should show. Built on FLOWS so it stays in lockstep with the quiz.
//
// Returned shape: [{ key, title, questionIds }]. Question 1 (user type) is the
// persona section's header control and is intentionally excluded here.
import { FLOWS } from './questions.js'

const PERSONA_TITLE = {
  student: 'Student',
  gamer: 'Gamer',
  office: 'Office',
}

export function profileSections(answers) {
  const a = answers || {}
  const sections = []

  const userType = a[1]
  if (userType === 'student') {
    const ids = [...FLOWS.student]
    // A student who games "regularly" unlocks the gamer questions (matches the
    // quiz's Q2 -> goto 5 jump).
    if (a[2] === 'regularly') ids.push(...FLOWS.gamer)
    sections.push({ key: 'student', title: PERSONA_TITLE.student, questionIds: ids })
  } else if (userType === 'gamer') {
    sections.push({ key: 'gamer', title: PERSONA_TITLE.gamer, questionIds: [...FLOWS.gamer] })
  } else if (userType === 'office') {
    sections.push({ key: 'office', title: PERSONA_TITLE.office, questionIds: [...FLOWS.office] })
  }

  // "About you" (closing) — Q16 (wired-too) is a conditional follow-up to Q15.
  const about = []
  for (const id of FLOWS.closing) {
    about.push(id)
    if (id === 15 && (a[15] === 'yes' || a[15] === 'preferably')) about.push(16)
  }
  sections.push({ key: 'about', title: 'About you', questionIds: about })

  return sections
}
