// Questionnaire content + flow definitions.
//
// FLOWS are ordered lists of question ids. The traversal engine treats a
// "jump" as a call: it pushes a sub-flow, runs it to that flow's end, then
// returns to finish the original flow. See engine.js.
//
//   Opening (everyone) -> persona flow -> shared Closing (everyone)
//
// Example path (student who games regularly):
//   1 -> 2 ->(jump 5) 5,6,7,8 ->(return) 3,4 -> 13,14,15,(16),17,18

export const FLOWS = {
  student: [2, 3, 4],
  // Grip (19) + sensitivity/latency (20) are gamer questions. Students who game
  // regularly run this flow too (Q2 "regularly" jumps into it), so they get them.
  gamer: [5, 6, 7, 8, 19, 20],
  office: [9, 10, 11, 12],
  closing: [13, 14, 15, 17, 18, 21], // 16 is a conditional follow-up pushed by Q15
}

export const QUESTIONS = {
  // ---- Opening (everyone) ----------------------------------------------- //
  1: {
    id: 1,
    section: 'Getting started',
    type: 'select',
    text: 'Who will be the main user of this mouse?',
    // Each persona enters its own flow, then the shared closing flow. Closing
    // is pushed first so it runs once, after the persona flow completes.
    options: [
      { label: 'A student', value: 'student', enter: ['closing', 'student'] },
      { label: 'A gamer', value: 'gamer', enter: ['closing', 'gamer'] },
      { label: 'An office / professional user', value: 'office', enter: ['closing', 'office'] },
    ],
  },

  // ---- Student ---------------------------------------------------------- //
  2: {
    id: 2,
    section: 'Student',
    type: 'select',
    text: 'In your free time, do you play computer games?',
    options: [
      { label: 'Yes, regularly', value: 'regularly', goto: 5 },
      { label: 'Once in a while', value: 'sometimes' },
      { label: 'Not really', value: 'no' },
    ],
  },
  3: {
    id: 3,
    section: 'Student',
    type: 'select',
    text: 'How often do you carry your laptop and mouse between places (class, library, home)?',
    options: [
      { label: 'Almost every day', value: 'daily' },
      { label: 'A few times a week', value: 'weekly' },
      { label: 'Occasionally', value: 'occasionally' },
      { label: 'Rarely', value: 'rarely' },
      { label: 'Never', value: 'never' },
    ],
  },
  4: {
    id: 4,
    section: 'Student',
    type: 'select',
    text: 'Would shortcut buttons (back/forward, copy/paste) make studying easier?',
    options: [
      { label: 'Yes, that sounds useful', value: 'yes' },
      { label: 'No, I prefer a simple mouse', value: 'no' },
    ],
  },

  // ---- Gamer ------------------------------------------------------------ //
  5: {
    id: 5,
    section: 'Gamer',
    type: 'select',
    text: 'Which game genre do you play the most?',
    options: [
      { label: 'FPS (first-person shooters)', value: 'fps' },
      { label: 'MMORPG', value: 'mmorpg' },
      { label: 'RTS (real-time strategy)', value: 'rts' },
      { label: 'MOBA', value: 'moba' },
      { label: 'A mix of genres / other', value: 'other' },
    ],
  },
  6: {
    id: 6,
    section: 'Gamer',
    type: 'select',
    text: 'How much does a lightweight mouse matter to you?',
    options: [
      { label: 'A lot — the lighter, the better', value: 'high' },
      { label: 'Somewhat', value: 'medium' },
      { label: 'Not really', value: 'low' },
    ],
  },
  7: {
    id: 7,
    section: 'Gamer',
    type: 'select',
    text: 'Do you want RGB lighting?',
    options: [
      { label: 'Yes, I love it', value: 'yes' },
      { label: "I don't mind either way", value: 'either' },
      { label: 'No, keep it clean', value: 'no' },
    ],
  },
  8: {
    id: 8,
    section: 'Gamer',
    type: 'select',
    text: 'How would you describe your play style?',
    options: [
      { label: 'Competitive — I chase every bit of performance', value: 'competitive' },
      { label: 'Casual — comfort matters more than raw specs', value: 'casual' },
    ],
  },

  // ---- Office / professional -------------------------------------------- //
  9: {
    id: 9,
    section: 'Office',
    type: 'select',
    text: 'Do you need programmable buttons for shortcuts or macros?',
    options: [
      { label: 'Yes, I rely on them', value: 'yes' },
      { label: 'Occasionally handy', value: 'sometimes' },
      { label: 'No', value: 'no' },
    ],
  },
  10: {
    id: 10,
    section: 'Office',
    type: 'select',
    text: 'Is your mouse mostly used at one fixed desk, or do you move around?',
    options: [
      { label: 'A fixed desk', value: 'fixed' },
      { label: 'I move between places', value: 'mobile' },
      { label: 'A bit of both', value: 'both' },
    ],
  },
  11: {
    id: 11,
    section: 'Office',
    type: 'slider',
    text: 'On a typical day, how many hours do you use your mouse?',
    min: 0,
    max: 24,
    step: 1,
    unit: 'h',
    default: 6,
  },
  12: {
    id: 12,
    section: 'Office',
    type: 'select',
    text: 'Do you feel wrist or hand strain during long sessions?',
    options: [
      { label: 'Often', value: 'often' },
      { label: 'Sometimes', value: 'sometimes' },
      { label: 'Rarely or never', value: 'rarely' },
    ],
  },

  // ---- Closing (everyone) ----------------------------------------------- //
  13: {
    id: 13,
    section: 'About you',
    type: 'select',
    text: "What's your hand size?",
    options: [
      { label: 'Large', value: 'large' },
      { label: 'Medium', value: 'medium' },
      { label: 'Small', value: 'small' },
    ],
  },
  14: {
    id: 14,
    section: 'About you',
    type: 'select',
    text: 'Which hand do you use your mouse with?',
    options: [
      { label: 'Right hand', value: 'right' },
      { label: 'Left hand', value: 'left' },
      { label: 'I switch / either', value: 'either' },
    ],
  },
  15: {
    id: 15,
    section: 'About you',
    type: 'select',
    text: 'Do you prefer a wireless mouse?',
    options: [
      { label: 'Yes, wireless', value: 'yes', push: [16] },
      { label: 'Preferably', value: 'preferably', push: [16] },
      { label: 'No, wired is fine', value: 'no' },
    ],
  },
  16: {
    id: 16,
    section: 'About you',
    type: 'select',
    text: 'Even when wireless, would you like the option to plug in a cable when needed?',
    options: [
      { label: "Yes, I'd like both options", value: 'yes' },
      { label: 'No, fully wireless is fine', value: 'no' },
    ],
  },
  17: {
    id: 17,
    section: 'About you',
    type: 'range',
    text: "What's your budget?",
    min: 0,
    max: 300,
    step: 5,
    unit: '$',
    defaultMin: 20,
    defaultMax: 150,
  },
  18: {
    id: 18,
    section: 'About you',
    type: 'multiselect',
    optional: true,
    text: 'Any brands you lean toward? (optional)',
    options: [
      { label: 'Logitech', value: 'Logitech' },
      { label: 'Razer', value: 'Razer' },
      { label: 'No preference', value: 'none', exclusive: true },
    ],
  },

  // ---- Gamer (also students who game) ----------------------------------- //
  19: {
    id: 19,
    section: 'Gamer',
    type: 'select',
    text: 'How do you usually hold your mouse?',
    options: [
      { label: 'Palm grip — whole hand rests on it', value: 'palm' },
      { label: 'Claw grip — arched fingers', value: 'claw' },
      { label: 'Fingertip grip — fingers only', value: 'fingertip' },
      { label: 'Not sure', value: 'unsure' },
    ],
  },
  20: {
    id: 20,
    section: 'Gamer',
    type: 'select',
    text: 'How much do you prioritise high sensitivity (DPI) and low latency (polling rate)?',
    options: [
      { label: 'A lot — I want top sensitivity and the fastest response', value: 'high' },
      { label: 'Somewhat', value: 'medium' },
      { label: 'Not important', value: 'low' },
    ],
  },

  // ---- Closing (everyone) ----------------------------------------------- //
  21: {
    id: 21,
    section: 'About you',
    type: 'select',
    text: 'Do you have a preferred colour?',
    options: [
      { label: 'Black', value: 'Black' },
      { label: 'White', value: 'White' },
      { label: 'Pink', value: 'Pink' },
      { label: 'No preference', value: 'none' },
    ],
  },
}
