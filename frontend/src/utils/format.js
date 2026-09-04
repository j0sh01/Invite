export function formatDate(date, opts = {}) {
  if (!date) return ''
  const d = new Date(date)
  if (isNaN(d.getTime())) return String(date)
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    ...opts,
  })
}

export function formatLongDate(date) {
  return formatDate(date, {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  })
}

export function formatTime(time) {
  if (!time) return ''
  // Handles HH:MM[:SS] values coming straight from Frappe Time fields
  const match = String(time).match(/^(\d{1,2}):(\d{2})/)
  if (!match) return String(time)
  const [_, h, m] = match
  const hour = parseInt(h, 10)
  const ampm = hour >= 12 ? 'PM' : 'AM'
  const hour12 = hour % 12 === 0 ? 12 : hour % 12
  return `${hour12}:${m} ${ampm}`
}

export function formatDateTime(dt, opts = {}) {
  if (!dt) return ''
  const d = new Date(dt)
  if (isNaN(d.getTime())) return String(dt)
  return d.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    ...opts,
  })
}

export function pluralize(count, singular, plural) {
  const n = Number(count) || 0
  return `${n} ${n === 1 ? singular : plural || singular + 's'}`
}

export function initials(name = '') {
  return String(name)
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join('')
}
