/**
 * Client-side mirror of backend/app/compute.py.
 *
 * The table editor shows derived values (service periods, ages, leave days) as
 * they are typed, so the rules have to match the server exactly — the server
 * remains the authority when the documents are rendered.
 *
 * Government convention: a period written "from A to B" includes B, so the
 * length is measured from A to B + 1 day.
 */

/** Accept dd-mm-yyyy, dd/mm/yyyy or yyyy-mm-dd. Returns a Date or null. */
export function parseDate(value) {
  if (!value) return null
  if (value instanceof Date) return value
  const s = String(value).trim()
  let m = s.match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$/)
  if (m) return makeDate(+m[1], +m[2], +m[3])
  m = s.match(/^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$/)
  if (m) return makeDate(+m[3], +m[2], +m[1])
  return null
}

function makeDate(year, month, day) {
  const d = new Date(year, month - 1, day)
  // Reject impossible dates such as 31-02-2020.
  if (d.getFullYear() !== year || d.getMonth() !== month - 1 || d.getDate() !== day) return null
  return d
}

export function formatDate(value) {
  const d = parseDate(value)
  if (!d) return ''
  const pad = (n) => String(n).padStart(2, '0')
  return `${pad(d.getDate())}-${pad(d.getMonth() + 1)}-${d.getFullYear()}`
}

const pad2 = (n) => String(n).padStart(2, '0')

/** Y/M/D between two dates; `inclusive` counts the end date as served. */
export function durationBetween(start, end, inclusive = true) {
  const a = parseDate(start)
  let b = parseDate(end)
  if (!a || !b) return null
  if (inclusive) b = new Date(b.getFullYear(), b.getMonth(), b.getDate() + 1)
  if (b < a) return null

  let y = b.getFullYear() - a.getFullYear()
  let m = b.getMonth() - a.getMonth()
  let d = b.getDate() - a.getDate()
  if (d < 0) {
    m -= 1
    const prevMonthEnd = new Date(b.getFullYear(), b.getMonth(), 0)
    d += prevMonthEnd.getDate()
  }
  if (m < 0) { y -= 1; m += 12 }
  return { y, m, d, dashed: `${pad2(y)}-${pad2(m)}-${pad2(d)}` }
}

/** Sum of Y/M/D durations, normalised on 30-day months and 360-day years. */
export function sumDurations(list) {
  let y = 0, m = 0, d = 0
  for (const item of list) {
    if (!item) continue
    y += item.y; m += item.m; d += item.d
  }
  m += Math.floor(d / 30); d %= 30
  y += Math.floor(m / 12); m %= 12
  return { y, m, d, dashed: `${pad2(y)}-${pad2(m)}-${pad2(d)}` }
}

/** Completed six-monthly periods; 3 months or more counts as one, capped at 66. */
export function sixMonthlyPeriods(dur) {
  if (!dur) return 0
  const months = dur.y * 12 + dur.m
  let periods = Math.floor(months / 6)
  const remainder = months % 6
  if (remainder >= 3 || (remainder === 2 && dur.d >= 15)) periods += 1
  return Math.min(periods, 66)
}

/** Age in completed years on a reference date (defaults to today). */
export function ageOn(dob, on) {
  const d = parseDate(dob)
  if (!d) return ''
  const ref = parseDate(on) || new Date()
  let age = ref.getFullYear() - d.getFullYear()
  const beforeBirthday =
    ref.getMonth() < d.getMonth() ||
    (ref.getMonth() === d.getMonth() && ref.getDate() < d.getDate())
  if (beforeBirthday) age -= 1
  return age
}

/** Inclusive day count between two dates, as the leave statement counts them. */
export function daysBetween(start, end) {
  const a = parseDate(start)
  const b = parseDate(end)
  if (!a || !b || b < a) return ''
  return Math.round((b - a) / 86400000) + 1
}

export function indianNumber(value) {
  const n = Math.round(Number(String(value ?? '').replace(/[, /-]/g, '')))
  if (!Number.isFinite(n)) return ''
  const sign = n < 0 ? '-' : ''
  const s = String(Math.abs(n))
  if (s.length <= 3) return sign + s
  const tail = s.slice(-3)
  let head = s.slice(0, -3)
  const parts = []
  while (head.length > 2) { parts.unshift(head.slice(-2)); head = head.slice(0, -2) }
  if (head) parts.unshift(head)
  return sign + parts.concat(tail).join(',')
}

/**
 * Derived value for one row, described by the table's `computed` entry.
 * Returns a string, or '' when the inputs are not complete yet.
 */
export function deriveCell(spec, row, context = {}) {
  switch (spec.kind) {
    case 'duration': {
      const dur = durationBetween(row[spec.from], row[spec.to])
      return dur ? dur.dashed : ''
    }
    case 'days': {
      const days = daysBetween(row[spec.from], row[spec.to])
      return days === '' ? '' : String(days)
    }
    case 'age': {
      const age = ageOn(row[spec.from], context.onDate)
      return age === '' ? '' : String(age)
    }
    default:
      return ''
  }
}

/** Total row shown under a table, when the table declares one. */
export function deriveTotal(spec, rows, context = {}) {
  if (!rows?.length) return ''
  if (spec.kind === 'duration') {
    const parts = rows.map((r) => durationBetween(r[spec.from], r[spec.to])).filter(Boolean)
    return parts.length ? sumDurations(parts).dashed : ''
  }
  if (spec.kind === 'days') {
    const total = rows.reduce((sum, r) => {
      const typed = String(r[spec.target] ?? '').trim()
      const value = typed !== '' ? Number(typed) : daysBetween(r[spec.from], r[spec.to])
      return sum + (Number.isFinite(Number(value)) ? Number(value) : 0)
    }, 0)
    return total ? String(total) : ''
  }
  return deriveCell(spec, rows[rows.length - 1], context)
}
