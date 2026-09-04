// Centralized tone mapping so every page renders statuses the same way.
// Backend records carry color names (blue/orange/purple/yellow/green/red)
// or direct status names — both resolve to the same visual language.
//
// Note: "blue" (as used by Event Status records) renders with the app's
// terracotta accent instead of a cold blue, keeping the palette warm.

const FRONTEND_DOT = {
  ember: 'bg-[#C75F2C]',
  orange: 'bg-[#EA580C]',
  purple: 'bg-[#9333EA]',
  yellow: 'bg-[#D97706]',
  green: 'bg-[#16A34A]',
  red: 'bg-[#DC2626]',
  gray: 'bg-[#A39277]',
}

const FRONTEND_PILL = {
  ember: 'bg-[#FBF2EC] text-[#8F3B1C]',
  orange: 'bg-[#FFF3E7] text-[#9A3412]',
  purple: 'bg-[#FAF3FF] text-[#6B21A8]',
  yellow: 'bg-[#FDF6E3] text-[#92400E]',
  green: 'bg-[#F0F7F2] text-[#166534]',
  red: 'bg-[#FEF1F1] text-[#991B1B]',
  gray: 'bg-[#F3EDE1] text-[#5E503B]',
}

// Known statuses → color name
export const STATUS_COLORS = {
  // Event lifecycle
  Planning: 'blue',
  'Invitations Sent': 'orange',
  'RSVPs Open': 'purple',
  Ongoing: 'yellow',
  Completed: 'green',
  Cancelled: 'red',
  // Invitation / delivery
  Draft: 'gray',
  Ready: 'blue',
  Sent: 'blue',
  Delivered: 'green',
  Failed: 'red',
  Pending: 'gray',
  // RSVP
  Accepted: 'green',
  Declined: 'red',
  Maybe: 'yellow',
  // Guest invitation status
  'Not Sent': 'gray',
  // Check-in
  CheckedIn: 'green',
  Duplicate: 'yellow',
}

// Color name → resolved tone (blue maps onto the terracotta accent)
const COLOR_TO_TONE = {
  blue: 'ember',
  ember: 'ember',
  orange: 'orange',
  purple: 'purple',
  yellow: 'yellow',
  green: 'green',
  red: 'red',
  gray: 'gray',
}

export function resolveTone(statusOrColor) {
  if (!statusOrColor) return 'gray'
  const direct = STATUS_COLORS[statusOrColor]
  if (direct) return COLOR_TO_TONE[direct] || 'gray'
  const key = String(statusOrColor).toLowerCase()
  return COLOR_TO_TONE[key] || 'gray'
}

export function toneClasses(statusOrColor) {
  const tone = resolveTone(statusOrColor)
  return {
    dot: FRONTEND_DOT[tone] || FRONTEND_DOT.gray,
    pill: FRONTEND_PILL[tone] || FRONTEND_PILL.gray,
  }
}

export function eventStatusTone(status) {
  return toneClasses(status)
}
