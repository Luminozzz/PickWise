export function ArrowUp({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M12 19V5M12 5l-6 6M12 5l6 6"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export function ArrowDown({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M12 5v14M12 19l-6-6M12 19l6-6"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export function ArrowRight({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M5 12h14M13 6l6 6-6 6"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export function Minus({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M6 12h12" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" />
    </svg>
  )
}

// Stacked rows — the "list view" toggle icon.
export function Rows({ size = 20 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M4 6h16M4 12h16M4 18h16"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  )
}

// Filter — sliders.
export function Sliders({ size = 20 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M4 7h10M18 7h2M4 17h2M10 17h10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <circle cx="16" cy="7" r="2.4" stroke="currentColor" strokeWidth="2" />
      <circle cx="8" cy="17" r="2.4" stroke="currentColor" strokeWidth="2" />
    </svg>
  )
}

// Sort — tapering bars, the conventional "sort by amount" mark. Deliberately
// carries no arrow: it marks the states with no direction to point in (Featured,
// Top rated), and an arrow here would collide with ArrowUp / ArrowDown, which
// are what ascending and descending mean in this control.
export function Sort({ size = 20 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M4 7h16M4 12h10M4 17h5"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  )
}

// Info — marks a term that has an explanation behind it. Thin ring, short stem,
// separate dot, so it stays legible at 16px where a filled glyph would go muddy.
export function Info({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.7" />
      <path d="M12 11.2v5" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" />
      <circle cx="12" cy="7.6" r="1.05" fill="currentColor" />
    </svg>
  )
}

// Chevron down — dropdown affordance.
export function ChevronDown({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M6 9l6 6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function User({ size = 20 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="8" r="4" stroke="currentColor" strokeWidth="2" />
      <path
        d="M4 20c0-3.314 3.582-6 8-6s8 2.686 8 6"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  )
}

export function Grid({ size = 20 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M4 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM14 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zM14 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinejoin="round"
      />
    </svg>
  )
}

// AI "sparkle" star — a single centred four-point star.
export function Sparkle({ size = 20 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M12 3c.5 4.5 4 8 9 9-5 1-8.5 4.5-9 9-.5-4.5-4-8-9-9 5-1 8.5-4.5 9-9z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinejoin="round"
      />
    </svg>
  )
}
// ---- category art ------------------------------------------------------------ //
//
// Bigger and more detailed than the icons above, because these carry a card rather
// than sit beside a label. Drawn on a 48 grid for that detail, stroked in
// currentColor so a card can tint them on hover, and outlined to match the set.

// Mouse, from above: body, the split between the buttons and the palm, and the
// wheel sitting in the upper half.
export function Mouse({ size = 48 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none" aria-hidden="true">
      <path
        d="M24 3.5c8 0 13 6 13 15v9c0 9.7-5.8 17-13 17s-13-7.3-13-17v-9c0-9 5-15 13-15z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinejoin="round"
      />
      <path d="M11.4 21.5h25.2" stroke="currentColor" strokeWidth="1.5" />
      <rect
        x="22.2"
        y="8.5"
        width="3.6"
        height="9"
        rx="1.8"
        stroke="currentColor"
        strokeWidth="1.5"
      />
    </svg>
  )
}

// Keyboard: two rows of keys and a spacebar.
export function Keyboard({ size = 48 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none" aria-hidden="true">
      <rect x="3" y="13" width="42" height="22" rx="4" stroke="currentColor" strokeWidth="2" />
      <path
        d="M9 19.5h3M15.5 19.5h3M22 19.5h3M28.5 19.5h3M35 19.5h4M9 25h3M15.5 25h3M22 25h3M28.5 25h3M35 25h4M16 30.5h16"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  )
}

// Monitor: panel on a stem and a foot.
export function Monitor({ size = 48 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none" aria-hidden="true">
      <rect x="4" y="8" width="40" height="26" rx="3" stroke="currentColor" strokeWidth="2" />
      <path
        d="M24 34v5M16 40h16"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  )
}

// Laptop: the lid is open at the bottom so the base draws that edge once rather
// than both stroking it and doubling its weight.
export function Laptop({ size = 48 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none" aria-hidden="true">
      <path
        d="M7 30V13a2 2 0 012-2h30a2 2 0 012 2v17"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinejoin="round"
      />
      <path
        d="M3.5 30h41l-2.6 5.2a2 2 0 01-1.8 1.1H7.9a2 2 0 01-1.8-1.1L3.5 30z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinejoin="round"
      />
    </svg>
  )
}

// Keyed by category slug, so the landing page and the coming soon page pull the
// same art from one place.
export const CATEGORY_ICON = {
  mouse: Mouse,
  keyboard: Keyboard,
  monitor: Monitor,
  laptop: Laptop,
}
