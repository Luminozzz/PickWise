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
//
// User-facing copy (section names, question text, option labels) is title case.

export const FLOWS = {
  student: [2, 3, 4],
  // Grip (19) + sensitivity/latency (20) are gamer questions. Students who game
  // regularly run this flow too (Q2 "regularly" jumps into it), so they get them.
  gamer: [5, 6, 7, 8, 19, 20],
  office: [9, 10, 11, 12],
  closing: [13, 14, 15, 17, 22, 18, 21], // 16 is a conditional follow-up pushed by Q15
}

export const QUESTIONS = {
  // ---- Opening (everyone) ----------------------------------------------- //
  1: {
    id: 1,
    section: 'Getting Started',
    type: 'select',
    text: 'Who Will Be the Main User of This Mouse?',
    // Each persona enters its own flow, then the shared closing flow. Closing
    // is pushed first so it runs once, after the persona flow completes.
    // Skipping enters only the closing flow (general questions, no persona rules).
    skip: { enter: ['closing'] },
    options: [
      { label: 'A Student', value: 'student', enter: ['closing', 'student'] },
      { label: 'A Gamer', value: 'gamer', enter: ['closing', 'gamer'] },
      { label: 'An Office / Professional User', value: 'office', enter: ['closing', 'office'] },
    ],
  },

  // ---- Student ---------------------------------------------------------- //
  2: {
    id: 2,
    section: 'Student',
    type: 'select',
    text: 'In Your Free Time, Do You Play Computer Games?',
    options: [
      { label: 'Yes, Regularly', value: 'regularly', goto: 5 },
      { label: 'Once in a While', value: 'sometimes' },
      { label: 'Not Really', value: 'no' },
    ],
  },
  3: {
    id: 3,
    section: 'Student',
    type: 'select',
    text: 'How Often Do You Carry Your Laptop and Mouse Between Places (Class, Library, Home)?',
    options: [
      { label: 'Almost Every Day', value: 'daily' },
      { label: 'A Few Times a Week', value: 'weekly' },
      { label: 'Occasionally', value: 'occasionally' },
      { label: 'Rarely', value: 'rarely' },
      { label: 'Never', value: 'never' },
    ],
  },
  4: {
    id: 4,
    section: 'Student',
    type: 'select',
    text: 'Would Shortcut Buttons (Back/Forward, Copy/Paste) Make Studying Easier?',
    help: [
      {
        term: 'Shortcut buttons',
        text: 'Extra buttons, usually on the side by your thumb, that you can set to actions like back, forward, copy or paste.',
      },
    ],
    options: [
      { label: 'Yes, That Sounds Useful', value: 'yes' },
      { label: 'No, I Prefer a Simple Mouse', value: 'no' },
    ],
  },

  // ---- Gamer ------------------------------------------------------------ //
  5: {
    id: 5,
    section: 'Gamer',
    type: 'select',
    text: 'Which Game Genre Do You Play the Most?',
    // Genre names are the technical terms here, so the help sits on each option
    // rather than on the question.
    options: [
      {
        label: 'FPS (First-Person Shooters)',
        value: 'fps',
        help: 'First person shooters like Valorant or CS2. Aiming is the main skill, so a light mouse and an accurate sensor help most.',
      },
      {
        label: 'MMORPG',
        value: 'mmorpg',
        help: 'Massively multiplayer online role playing games like World of Warcraft. You bind a lot of abilities to your mouse, so extra buttons matter more than low weight.',
      },
      {
        label: 'RTS (Real-Time Strategy)',
        value: 'rts',
        help: 'Real time strategy games like StarCraft. You click and drag across the map constantly, which rewards a responsive sensor.',
      },
      {
        label: 'MOBA',
        value: 'moba',
        help: 'Multiplayer online battle arena games like League of Legends or Dota 2. Quick, accurate clicks matter more than raw speed.',
      },
      { label: 'A Mix of Genres / Other', value: 'other' },
    ],
  },
  6: {
    id: 6,
    section: 'Gamer',
    type: 'select',
    text: 'How Much Does a Lightweight Mouse Matter to You?',
    help: [
      {
        term: 'Lightweight',
        text: 'Mouse weight in grams. A lighter mouse is easier to move quickly and causes less fatigue over a long session, while a heavier one can feel steadier. Anything under about 80g counts as light.',
      },
    ],
    options: [
      { label: 'A Lot — the Lighter, the Better', value: 'high' },
      { label: 'Somewhat', value: 'medium' },
      { label: 'Not Really', value: 'low' },
    ],
  },
  7: {
    id: 7,
    section: 'Gamer',
    type: 'select',
    text: 'Do You Want RGB Lighting?',
    help: [
      {
        term: 'RGB',
        text: 'Colour changing LED lighting built into the mouse. It is cosmetic and does not affect how the mouse tracks, though on a wireless mouse it will drain the battery faster.',
      },
    ],
    options: [
      { label: 'Yes, I Love It', value: 'yes' },
      { label: "I Don't Mind Either Way", value: 'either' },
      { label: 'No, Keep It Clean', value: 'no' },
    ],
  },
  8: {
    id: 8,
    section: 'Gamer',
    type: 'select',
    text: 'How Would You Describe Your Play Style?',
    options: [
      { label: 'Competitive — I Chase Every Bit of Performance', value: 'competitive' },
      { label: 'Casual — Comfort Matters More Than Raw Specs', value: 'casual' },
    ],
  },

  // ---- Office / professional -------------------------------------------- //
  9: {
    id: 9,
    section: 'Office',
    type: 'select',
    text: 'Do You Need Programmable Buttons for Shortcuts or Macros?',
    help: [
      {
        term: 'Macro',
        text: 'A macro is a sequence of actions saved to a single button. It could be a copy and paste, going back to a previous page, or opening an app. Programmable buttons are the extra buttons you assign them to.',
      },
    ],
    options: [
      { label: 'Yes, I Rely on Them', value: 'yes' },
      { label: 'Occasionally Handy', value: 'sometimes' },
      { label: 'No', value: 'no' },
    ],
  },
  10: {
    id: 10,
    section: 'Office',
    type: 'select',
    text: 'Is Your Mouse Mostly Used at One Fixed Desk, or Do You Move Around?',
    options: [
      { label: 'A Fixed Desk', value: 'fixed' },
      { label: 'I Move Between Places', value: 'mobile' },
      { label: 'A Bit of Both', value: 'both' },
    ],
  },
  11: {
    id: 11,
    section: 'Office',
    type: 'slider',
    text: 'On a Typical Day, How Many Hours Do You Use Your Mouse?',
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
    text: 'Do You Feel Wrist or Hand Strain During Long Sessions?',
    options: [
      { label: 'Often', value: 'often' },
      { label: 'Sometimes', value: 'sometimes' },
      { label: 'Rarely or Never', value: 'rarely' },
    ],
  },

  // ---- Closing (everyone) ----------------------------------------------- //
  13: {
    id: 13,
    section: 'About You',
    type: 'select',
    text: "What's Your Hand Size?",
    help: [
      {
        term: 'Hand size',
        text: 'Measure from your wrist crease to the tip of your middle finger. In general, under 17cm is small, 17 to 19cm is medium, and above 19cm is large. This decides which mouse lengths will feel comfortable.',
      },
    ],
    options: [
      { label: 'Large', value: 'large' },
      { label: 'Medium', value: 'medium' },
      { label: 'Small', value: 'small' },
    ],
  },
  14: {
    id: 14,
    section: 'About You',
    type: 'select',
    text: 'Which Hand Do You Use Your Mouse With?',
    options: [
      { label: 'Right Hand', value: 'right' },
      { label: 'Left Hand', value: 'left' },
      { label: 'I Switch / Either', value: 'either' },
    ],
  },
  15: {
    id: 15,
    section: 'About You',
    type: 'select',
    text: 'Do You Prefer a Wireless Mouse?',
    help: [
      {
        term: 'Wireless',
        text: 'Wireless mice connect either through a small USB dongle or over Bluetooth. A dongle is more responsive and better for gaming. Bluetooth saves a USB port and is handier for travel, but it usually has higher latency.',
      },
    ],
    options: [
      { label: 'Yes, Wireless', value: 'yes', push: [16] },
      { label: 'Preferably', value: 'preferably', push: [16] },
      { label: 'No, Wired Is Fine', value: 'no' },
    ],
  },
  16: {
    id: 16,
    section: 'About You',
    type: 'select',
    text: 'Even When Wireless, Would You Like the Option to Plug in a Cable When Needed?',
    options: [
      { label: "Yes, I'd Like Both Options", value: 'yes' },
      { label: 'No, Fully Wireless Is Fine', value: 'no' },
    ],
  },
  17: {
    id: 17,
    section: 'About You',
    type: 'range',
    text: "What's Your Budget?",
    min: 0,
    max: 300,
    step: 5,
    unit: '$',
    defaultMin: 20,
    defaultMax: 150,
  },
  18: {
    id: 18,
    section: 'About You',
    type: 'multiselect',
    optional: true,
    text: 'Any Brands You Lean Toward? (Optional)',
    // Every brand the catalogue actually stocks, ordered by how many mice each has
    // so the likeliest choices come first. Values are the exact `brand_name`
    // spellings from the database — the catalogue's brand filter compares against
    // that column directly, so a mismatch here would silently match nothing.
    options: [
      { label: 'Logitech', value: 'Logitech' },
      { label: 'Asus', value: 'Asus' },
      { label: 'Razer', value: 'Razer' },
      { label: 'HP', value: 'HP' },
      { label: 'UGreen', value: 'UGreen' },
      { label: 'HyperX', value: 'HyperX' },
      { label: 'No Preference', value: 'none', exclusive: true },
    ],
  },

  // ---- Gamer (also students who game) ----------------------------------- //
  19: {
    id: 19,
    section: 'Gamer',
    type: 'select',
    text: 'How Do You Usually Hold Your Mouse?',
    // Grip names are the technical terms, so each option carries its own help.
    options: [
      {
        label: 'Palm Grip — Whole Hand Rests on It',
        value: 'palm',
        help: 'The most common way to hold a mouse. Your whole hand rests flat along it. This is the most relaxed hold and it suits larger, taller mice.',
      },
      {
        label: 'Claw Grip — Arched Fingers',
        value: 'claw',
        help: 'Your palm rests on the back of the mouse while your fingers arch up to the buttons. It sits between the other two grips and favours medium sized mice.',
      },
      {
        label: 'Fingertip Grip — Fingers Only',
        value: 'fingertip',
        help: 'Only your fingertips touch the mouse and your palm floats above it. This gives the quickest movements and suits small, light mice.',
      },
      { label: 'Not Sure', value: 'unsure' },
    ],
  },
  20: {
    id: 20,
    section: 'Gamer',
    type: 'select',
    text: 'How Much Do You Prioritise High Sensitivity (DPI) and Low Latency (Polling Rate)?',
    // Two terms, both in the question rather than in the options, so they share one
    // button and render as a paragraph each.
    help: [
      {
        term: 'DPI',
        text: 'Dots per inch. It sets how far the cursor travels for a given hand movement, so a higher DPI gives faster cursor speed and finer control over small adjustments. Most people use far less than a mouse’s maximum, so past a certain point a bigger number makes little difference.',
      },
      {
        term: 'Polling rate',
        text: 'How many times per second the mouse reports its position to your computer, measured in Hz. A higher rate means the cursor updates sooner, which reduces latency. Latency is the lag between moving your mouse and that movement showing up on screen. 1000Hz is the common standard and most people will not notice the difference above it. Rates of 4000Hz to 8000Hz are aimed at high end competitive play, and they make your computer work harder and use more battery on a wireless mouse.',
      },
    ],
    options: [
      { label: 'A Lot — I Want Top Sensitivity and the Fastest Response', value: 'high' },
      { label: 'Somewhat', value: 'medium' },
      { label: 'Not Important', value: 'low' },
    ],
  },

  // ---- Closing (everyone) ----------------------------------------------- //
  21: {
    id: 21,
    section: 'About You',
    type: 'select',
    text: 'Do You Have a Preferred Colour?',
    // Colour families rather than the raw `mouse_skins.colour` values. Those run to
    // 40 distinct strings, and most aren't answerable choices: duplicates
    // ("Off-white" and "Off White"), edition names that say nothing about colour
    // ("Faker Edition", "Minecraft Edition"), and one-offs ("Oat Milk"). Each family
    // below is one the catalogue genuinely carries, ordered by how many mice fall
    // into it, and each is a keyword `colourToHex` in colours.js already recognises.
    //
    // Black, White and Pink keep their original values so colour answers already
    // saved against a profile still match an option.
    options: [
      { label: 'Black', value: 'Black' },
      { label: 'White', value: 'White' },
      { label: 'Grey', value: 'Grey' },
      { label: 'Pink', value: 'Pink' },
      { label: 'Red', value: 'Red' },
      { label: 'Green', value: 'Green' },
      { label: 'Blue', value: 'Blue' },
      { label: 'Purple', value: 'Purple' },
      { label: 'No Preference', value: 'none' },
    ],
  },

  22: {
    id: 22,
    section: 'About You',
    type: 'select',
    text: 'When Price and Performance Pull in Different Directions, Which Do You Value More?',
    options: [
      { label: 'Price — I Want the Best Deal', value: 'price' },
      { label: 'Performance — I Want the Best Specs', value: 'performance' },
      { label: 'A Balance of Both', value: 'balance' },
    ],
  },
}
