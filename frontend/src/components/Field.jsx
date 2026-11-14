import DateInput from './DateInput'
import { useLang } from '../i18n'

/** Marathi and English labels, ordered by the current language. */
export function BiLabel({ mr, en }) {
  const { lang } = useLang()
  const [primary, secondary] = lang === 'mr' ? [mr, en] : [en, mr]
  return (
    <span className="lbl">
      <span className={'primary ' + (lang === 'mr' ? 'mr' : '')}>{primary}</span>
      {secondary && secondary !== primary && (
        <span className={'secondary ' + (lang === 'mr' ? '' : 'mr')}> {secondary}</span>
      )}
    </span>
  )
}

/** Marathi text needs the Devanagari face; ISO dates need a date input. */
const isMarathiField = (key) => /(_mr$|_mr_)/.test(key)

export function Field({ field, value, onChange, onConvert, converting,
                        onBlur, autofilled }) {
  const { key, label_en, label_mr, type, options } = field
  const marathi = isMarathiField(key)
  const common = {
    value: value ?? '',
    onChange: (e) => onChange(e.target.value),
    onBlur: onBlur ? () => onBlur(field) : undefined,
    className: [marathi ? 'mr' : '', autofilled ? 'autofilled' : '']
      .join(' ').trim() || undefined,
  }

  let control
  if (type === 'textarea') {
    control = <textarea rows={3} {...common} />
  } else if (type === 'select') {
    control = (
      <select {...common}>
        <option value="">—</option>
        {(options || []).map((opt) => <option key={opt} value={opt}>{opt}</option>)}
      </select>
    )
  } else if (type === 'date') {
    control = <DateInput value={value} onChange={onChange} onBlur={common.onBlur}
      className={common.className} />
  } else if (type === 'number') {
    control = <input type="text" inputMode="decimal" {...common} />
  } else if (type === 'duration') {
    control = <DurationInput value={value} onChange={onChange} />
  } else if (type === 'list') {
    control = <ListInput value={value} onChange={onChange} />
  } else {
    control = <input type="text" {...common} />
  }

  const pair = field.pair
  return (
    <label className={'field' + (autofilled ? ' is-autofilled' : '')}>
      <span className="lbl-row">
        <BiLabel mr={label_mr} en={label_en} />
        {autofilled && <span className="badge auto autochip">ƒx</span>}
        {pair && onConvert && (
          <button type="button" className="convert" disabled={converting || !value}
            title={pair.direction === 'mr2en'
              ? 'मराठीवरून इंग्रजी भरा / Fill the English from the Marathi'
              : 'इंग्रजीवरून मराठी भरा (तपासा) / Draft the Marathi from the English (check it)'}
            onClick={(e) => { e.preventDefault(); onConvert(field) }}>
            {pair.direction === 'mr2en' ? '→ EN' : '→ मरा'}
          </button>
        )}
      </span>
      {control}
    </label>
  )
}

/** Years / months / days, stored as {y, m, d}. */
function DurationInput({ value, onChange }) {
  const v = value && typeof value === 'object' ? value : { y: 0, m: 0, d: 0 }
  const set = (part) => (e) =>
    onChange({ ...v, [part]: Number(e.target.value || 0) })
  return (
    <div className="row" style={{ gap: 6, flexWrap: 'nowrap' }}>
      {['y', 'm', 'd'].map((part) => (
        <input
          key={part} type="number" min="0" value={v[part] ?? 0}
          onChange={set(part)} style={{ width: '33%' }}
          aria-label={{ y: 'years', m: 'months', d: 'days' }[part]}
        />
      ))}
    </div>
  )
}

/** A simple list of strings (identification marks). */
function ListInput({ value, onChange }) {
  const items = Array.isArray(value) ? value : []
  const setAt = (i, text) => onChange(items.map((item, idx) => (idx === i ? text : item)))
  return (
    <div>
      {items.map((item, i) => (
        <div key={i} className="row" style={{ gap: 4, marginBottom: 4, flexWrap: 'nowrap' }}>
          <input value={item} onChange={(e) => setAt(i, e.target.value)} />
          <button type="button" className="small danger"
            onClick={() => onChange(items.filter((_, idx) => idx !== i))}>×</button>
        </div>
      ))}
      <button type="button" className="small" onClick={() => onChange([...items, ''])}>+</button>
    </div>
  )
}
