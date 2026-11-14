import { useRef } from 'react'
import { formatDate, parseDate } from '../compute'

/**
 * A date field that can be typed or picked.
 *
 * The forms are filled from service books written as dd-mm-yyyy, and an
 * experienced clerk types that faster than any picker — so the text box stays
 * the primary control and keeps that format. The calendar button opens the
 * browser's own picker for the cases where the date is being looked up rather
 * than copied, and whatever it returns is written back as dd-mm-yyyy.
 */
export default function DateInput({ value, onChange, className, onBlur, placeholder }) {
  const picker = useRef(null)

  /** yyyy-mm-dd for the native input, from whatever the text box holds. */
  const isoValue = (() => {
    const d = parseDate(value)
    if (!d) return ''
    const pad = (n) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
  })()

  const openPicker = () => {
    const el = picker.current
    if (!el) return
    // showPicker is the reliable way to open the calendar without the input
    // being visible; older browsers fall back to focusing it.
    if (typeof el.showPicker === 'function') {
      try { el.showPicker(); return } catch { /* not allowed without a gesture */ }
    }
    el.focus()
    el.click()
  }

  const typed = String(value ?? '')
  const invalid = typed.trim() !== '' && !parseDate(typed)

  return (
    <span className="date-field">
      <input
        type="text"
        value={typed}
        onChange={(e) => onChange(e.target.value)}
        onBlur={onBlur}
        placeholder={placeholder || 'dd-mm-yyyy'}
        className={[className, invalid ? 'invalid' : ''].filter(Boolean).join(' ') || undefined}
        inputMode="numeric"
      />
      <button type="button" className="cal-btn" tabIndex={-1}
        title="कॅलेंडरमधून निवडा / Pick from the calendar"
        onClick={(e) => { e.preventDefault(); openPicker() }}>📅</button>
      <input
        ref={picker} type="date" className="date-picker" tabIndex={-1} aria-hidden="true"
        value={isoValue}
        onChange={(e) => { if (e.target.value) onChange(formatDate(e.target.value)) }}
      />
    </span>
  )
}
