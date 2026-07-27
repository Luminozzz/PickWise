// One definition per term, shared by everything that explains itself: the quiz
// questions, the quiz options, the product page's spec rows and the compare table.
//
// Five of these are asked about in the quiz and also shown as a spec, so they used
// to exist twice with slightly different wording. Sharing them means the wording has
// to answer both "what should I pick?" and "what does this number mean?", which is
// why a few read a little fuller than they would if they only had one job.
export const TERMS = {
  // ---- asked in the quiz, and shown as a spec ---------------------------- //
  dpi: {
    term: 'DPI',
    text: 'Dots per inch. It sets how far the cursor travels for a given hand movement, so a higher DPI gives faster cursor speed and finer control over small adjustments. Most people use far less than a mouse’s maximum, so past a certain point a bigger number makes little difference.',
  },
  polling: {
    term: 'Polling rate',
    text: 'How many times per second the mouse reports its position to your computer, measured in Hz. A higher rate means the cursor updates sooner, which reduces latency. Latency is the lag between moving your mouse and that movement showing up on screen. 1000Hz is the common standard and most people will not notice the difference above it. Rates of 4000Hz to 8000Hz are aimed at high end competitive play, and they make your computer work harder and use more battery on a wireless mouse.',
  },
  rgb: {
    term: 'RGB',
    text: 'Colour changing LED lighting built into the mouse. It is cosmetic and does not affect how the mouse tracks, though on a wireless mouse it will drain the battery faster.',
  },
  weight: {
    term: 'Weight',
    text: 'Mouse weight in grams. A lighter mouse is easier to move quickly and causes less fatigue over a long session, while a heavier one can feel steadier. Anything under about 80g counts as light.',
  },
  connectivity: {
    term: 'Connectivity',
    text: 'How the mouse connects. Wired means a cable. Wireless means either a small USB dongle or Bluetooth: a dongle is more responsive and better for gaming, while Bluetooth saves a USB port and is handier for travel but usually has higher latency. Wired plus wireless means it does both, so you can plug in when the battery runs low.',
  },

  // ---- asked in the quiz only -------------------------------------------- //
  shortcutButtons: {
    term: 'Shortcut buttons',
    text: 'Extra buttons, usually on the side by your thumb, that you can set to actions like back, forward, copy or paste.',
  },
  macro: {
    term: 'Macro',
    text: 'A macro is a sequence of actions saved to a single button. It could be a copy and paste, going back to a previous page, or opening an app. Programmable buttons are the extra buttons you assign them to.',
  },
  handSize: {
    term: 'Hand size',
    text: 'Measure from your wrist crease to the tip of your middle finger. In general, under 17cm is small, 17 to 19cm is medium, and above 19cm is large. This decides which mouse lengths will feel comfortable.',
  },
  fps: {
    term: 'FPS',
    text: 'First person shooters (FPS), like Valorant or CS2. Aiming is the main skill, so a light mouse and an accurate sensor help most.',
  },
  mmorpg: {
    term: 'MMORPG',
    text: 'Massively multiplayer online role playing games (MMORPG), like World of Warcraft. You bind a lot of abilities to your mouse, so extra buttons matter more than low weight.',
  },
  rts: {
    term: 'RTS',
    text: 'Real time strategy (RTS), like StarCraft. You click and drag across the map constantly, which rewards a responsive sensor.',
  },
  moba: {
    term: 'MOBA',
    text: 'Multiplayer online battle arena (MOBA), like League of Legends or Dota 2. Quick, accurate clicks matter more than raw speed.',
  },
  palmGrip: {
    term: 'Palm grip',
    text: 'The most common way to hold a mouse. Your whole hand rests flat along it. This is the most relaxed hold and it suits larger, taller mice.',
  },
  clawGrip: {
    term: 'Claw grip',
    text: 'Your palm rests on the back of the mouse while your fingers arch up to the buttons. It sits between the other two grips and favours medium sized mice.',
  },
  fingertipGrip: {
    term: 'Fingertip grip',
    text: 'Only your fingertips touch the mouse and your palm floats above it. This gives the quickest movements and suits small, light mice.',
  },

  // ---- shown as a spec only ---------------------------------------------- //
  tracking: {
    term: 'Tracking speed',
    text: 'Inches per second, sometimes listed as max speed. It is how fast you can move the mouse before the sensor stops keeping up, at which point the cursor no longer follows your hand properly. Normal desktop use is nowhere near these figures. It only starts to matter if you play at a low sensitivity, where turning around means sweeping the whole mouse across the mat in one fast motion.',
  },
  battery: {
    term: 'Battery life',
    text: 'How long the mouse runs between charges. The range is the manufacturer’s own figures, which vary with settings such as lighting and polling rate, so the low end is the heaviest use and the high end the lightest.',
  },
  dimensions: {
    term: 'Dimensions',
    text: 'Length, width and height. Length matters most for fit: measure your wrist crease to the tip of your middle finger, and as a rough guide hands under 17cm suit smaller mice and over 19cm suit larger ones.',
  },
  shape: {
    term: 'Shape',
    text: 'The contour of the body. Ergonomic is sculpted for the right hand and is usually the most comfortable for long sessions, though these tend to be bigger and heavier, which can make them slower to move when gaming. Symmetrical is the same on both sides. Ambidextrous is symmetrical and has usable buttons on both sides.',
  },
  leftHanded: {
    term: 'Left-handed use',
    text: 'Whether the shape and button placement suit the left hand. A symmetrical body is not automatically left friendly, since the side buttons are often only on the left of the mouse where a left hand cannot reach them comfortably.',
  },
  buttons: {
    term: 'Buttons',
    text: 'How many buttons the mouse has. Anything beyond the two main clicks and the wheel can usually be assigned to a shortcut or a macro.',
  },
  price: {
    term: 'Price',
    text: 'The lowest price we have seen recently across the stores we track. It changes over time and may not include shipping.',
  },
}

// Spec rows arrive from the backend carrying a `key`, so the help is keyed the same
// way. The product page and the compare table are built from the same _SPECS list,
// so both read this one map.
export const SPEC_HELP = {
  weight: TERMS.weight,
  max_DPI: TERMS.dpi,
  polling: TERMS.polling,
  tracking: TERMS.tracking,
  buttons: TERMS.buttons,
  connectivity: TERMS.connectivity,
  battery: TERMS.battery,
  size: TERMS.dimensions,
  ergonomy: TERMS.shape,
  rgb: TERMS.rgb,
  left: TERMS.leftHanded,
  price: TERMS.price,
}
