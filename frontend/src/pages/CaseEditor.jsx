import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { api } from '../api'
import { BiLabel, Field } from '../components/Field'
import PhotoUpload from '../components/PhotoUpload'
import TableEditor from '../components/TableEditor'
import Documents from './Documents'
import { useT } from '../i18n'

// Long enough that a name is not converted letter by letter, short enough that
// the English appears while the clerk is still looking at the field.
const LIVE_DELAY = 450

export default function CaseEditor({ notify, health }) {
  const { id } = useParams()
  const t = useT()
  const [params, setParams] = useSearchParams()

  const [schema, setSchema] = useState(null)
  const [record, setRecord] = useState(null)
  const [data, setData] = useState(null)
  const [tab, setTab] = useState(() => params.get('tab') || 'details')
  const [dirty, setDirty] = useState(false)
  const [saving, setSaving] = useState(false)
  const [converting, setConverting] = useState('')
  // Fields the system filled in from their Marathi counterpart, so they can be
  // marked on screen. Typing in one clears the mark.
  const [autofilled, setAutofilled] = useState(() => new Set())
  const dataRef = useRef(null)
  const autofilledRef = useRef(autofilled)

  useEffect(() => { dataRef.current = data }, [data])
  useEffect(() => { autofilledRef.current = autofilled }, [autofilled])

  const load = useCallback(async () => {
    try {
      const [s, c] = await Promise.all([api.schema(), api.getCase(id)])
      setSchema(s.schema)
      setRecord(c)
      setData(c.data)
      setDirty(false)
    } catch (e) {
      notify(e.message, 'err')
    }
  }, [id, notify])

  useEffect(() => { load() }, [load])

  // While a background rebuild is running, refresh until it finishes so the
  // Documents tab stops showing "rebuilding" on its own.
  useEffect(() => {
    if (record?.regen_state !== 'running') return undefined
    const timer = window.setInterval(() => {
      api.getCase(id).then(setRecord).catch(() => {})
    }, 4000)
    return () => window.clearInterval(timer)
  }, [record?.regen_state, id])

  // Warn before leaving with unsaved edits -- these forms take a while to fill.
  useEffect(() => {
    const handler = (e) => { if (dirty) { e.preventDefault(); e.returnValue = '' } }
    window.addEventListener('beforeunload', handler)
    return () => window.removeEventListener('beforeunload', handler)
  }, [dirty])

  const setField = (section, key, value, { auto = false } = {}) => {
    setData((d) => ({ ...d, [section]: { ...d[section], [key]: value } }))
    setDirty(true)
    setAutofilled((prev) => {
      const path = `${section}.${key}`
      if (auto === (prev.has(path))) return prev
      const next = new Set(prev)
      if (auto) next.add(path); else next.delete(path)
      return next
    })
  }

  const setTable = (key, rows) => {
    setData((d) => ({ ...d, tables: { ...d.tables, [key]: rows } }))
    setDirty(true)
  }

  const setRefs = (refs, auto) => {
    setData((d) => ({
      ...d,
      refs,
      meta: { ...d.meta, refs_auto: auto === undefined ? false : auto },
    }))
    setDirty(true)
  }

  /**
   * Fill the counterpart field in the other script.
   *
   * Marathi to English is a straight transliteration and is trustworthy;
   * the reverse is a draft, so the operator is told to check it.
   */
  /**
   * When a paired field loses focus, fill its counterpart if that is still
   * empty. Both directions are done: Marathi to English is a dependable
   * transliteration, and English to Marathi -- a guess, since English spelling
   * records neither vowel length nor which "t"/"d"/"n" is meant -- is offered
   * on the same amber background so it reads as a draft to be checked.
   */
  const autoFillPair = async (sectionKey, field) => {
    if (!field.pair) return
    const source = data[sectionKey]?.[field.key]
    const target = data[sectionKey]?.[field.pair.other]
    if (!source || (target || '').trim()) return
    try {
      const res = await api.transliterate(source, field.pair.direction)
      if (res.text) setField(sectionKey, field.pair.other, res.text, { auto: true })
    } catch { /* leave the field empty; the button is still there */ }
  }

  /**
   * The same fill, but while the name is being typed.
   *
   * A clerk types a name and watches the other script appear beside it, rather
   * than discovering it after moving on. Each keystroke restarts a short wait
   * so the conversion runs once the typing pauses, not per letter. A side that
   * a person has typed is never overwritten -- only an empty one, or one this
   * filled itself.
   *
   * Only a keystroke reaches here, never setField, so the two halves of a pair
   * cannot fill each other back and forth.
   */
  const liveTimers = useRef({})

  const liveFillPair = (sectionKey, field, source) => {
    if (!field.pair) return
    const path = `${sectionKey}.${field.pair.other}`
    window.clearTimeout(liveTimers.current[path])
    liveTimers.current[path] = window.setTimeout(async () => {
      const target = dataRef.current?.[sectionKey]?.[field.pair.other]
      const mine = autofilledRef.current.has(path)
      if ((target || '').trim() && !mine) return          // typed by a person
      if (!source.trim()) {
        if (mine) setField(sectionKey, field.pair.other, '', { auto: true })
        return
      }
      try {
        const res = await api.transliterate(source, field.pair.direction)
        if (res.text) setField(sectionKey, field.pair.other, res.text, { auto: true })
      } catch { /* the conversion button is still there */ }
    }, LIVE_DELAY)
  }

  /* Stop a pending conversion from landing after the screen has moved on. */
  useEffect(() => () => {
    Object.values(liveTimers.current).forEach(window.clearTimeout)
  }, [])

  const convertField = async (sectionKey, field) => {
    const source = data[sectionKey]?.[field.key]
    if (!source) return
    setConverting(field.key)
    try {
      const res = await api.transliterate(source, field.pair.direction)
      if (!res.text) { notify(t('convertEmpty'), 'err'); return }
      setField(sectionKey, field.pair.other, res.text, { auto: true })
      notify(res.reliable ? t('converted') : t('convertedDraft'),
             res.reliable ? 'ok' : 'warn')
    } catch (e) {
      notify(e.message, 'err')
    } finally {
      setConverting('')
    }
  }

  const save = async () => {
    setSaving(true)
    try {
      const updated = await api.updateCase(id, { data: dataRef.current })
      setRecord(updated)
      setData(updated.data)
      setDirty(false)
      notify(t('saved'), 'ok')
      return updated
    } catch (e) {
      notify(e.message, 'err')
      return null
    } finally {
      setSaving(false)
    }
  }

  if (!schema || !data) return <p className="muted">{t('loading')}</p>

  return (
    <div>
      <div className="row between" style={{ marginBottom: 12 }}>
        <div>
          <Link to="/" className="link">← {t('cases')}</Link>
          <h2 style={{ margin: '4px 0 0', fontSize: 18 }}>
            {record.case_no}
            <span className="muted" style={{ fontWeight: 400, fontSize: 14 }}>
              {' '}· <span className="mr">{record.employee_name_mr || '—'}</span>
            </span>
          </h2>
        </div>
        <div className="row">
          {dirty && <span className="badge ready">{t('unsaved')}</span>}
          <button className="primary" onClick={save} disabled={saving || !dirty}>
            {saving ? t('saving') : t('save')}
          </button>
        </div>
      </div>

      <ComputedStrip computed={record.computed} t={t} />

      <div className="tabs">
        {[['details', t('details')], ['tables', t('tables')],
          ['documents', t('documents')]].map(([key, label]) => (
          <button key={key} className={tab === key ? 'on' : ''}
            onClick={() => { setTab(key); setParams(key === 'details' ? {} : { tab: key }) }}>
            {label}</button>
        ))}
      </div>

      {tab === 'details' && (
        <>
          {schema.sections.map((section) => (
            <div className="card" key={section.key}>
              <h2><BiLabel mr={section.title_mr} en={section.title_en} /></h2>
              <div className="grid">
                {section.fields.map((field) => (
                  <Field
                    key={field.key} field={field}
                    value={data[section.key]?.[field.key]}
                    onChange={(v) => {
                      setField(section.key, field.key, v)
                      liveFillPair(section.key, field, v)
                    }}
                    onConvert={(f) => convertField(section.key, f)}
                    converting={converting === field.key}
                    onBlur={(f) => autoFillPair(section.key, f)}
                    autofilled={autofilled.has(`${section.key}.${field.key}`)}
                  />
                ))}
              </div>
            </div>
          ))}
          <PhotoUpload caseId={id} photo={data.employee?.photo}
            notify={notify}
            onChanged={(name) => {
              setData((d) => ({ ...d, employee: { ...d.employee, photo: name } }))
              load()
            }} />
          <RefsEditor refs={data.refs || []} auto={data.meta?.refs_auto !== false}
            onChange={setRefs} schema={schema} t={t} notify={notify} />
        </>
      )}

      {tab === 'tables' && schema.tables.map((table) => (
        <TableEditor
          key={table.key} table={table}
          rows={data.tables?.[table.key]}
          onChange={(rows) => setTable(table.key, rows)}
          onDate={data.meta?.letter_date}
        />
      ))}

      {tab === 'documents' && (
        <Documents caseId={id} caseNo={record.case_no} dirty={dirty} onSave={save}
          notify={notify} onGenerated={load} caseState={record} health={health} />
      )}

      {tab !== 'documents' && (
        <div className="card">
          <div className="row">
            <button className="primary" onClick={save} disabled={saving || !dirty}>
              {saving ? t('saving') : t('save')}
            </button>
            <span className="muted small">
              {dirty ? t('unsaved') : t('saved')}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

function ComputedStrip({ computed, t }) {
  if (!computed) return null
  const cells = [
    ['grossService', computed.gross_service?.dashed],
    ['qualifyingService', computed.net_qualifying?.dashed],
    ['sixMonthly', computed.six_monthly_periods],
    ['lastPay', computed.last_pay ? `₹ ${computed.last_pay.toLocaleString('en-IN')}` : '—'],
    ['ageAtRetirement', computed.age_at_retirement],
  ]
  return (
    <>
      <div className="computed-strip" style={{ marginBottom: 12 }}>
        {cells.map(([key, value]) => (
          <div className="cell" key={key}>
            <div className="k"><BiLabel mr={t.pair(key)[0]} en={t.pair(key)[1]} /></div>
            <div className="v">{value ?? '—'}</div>
          </div>
        ))}
        <div className="cell hi">
          <div className="k"><BiLabel mr={t.pair('gratuity')[0]} en={t.pair('gratuity')[1]} /></div>
          <div className="v">₹ {computed.gratuity_formatted || '—'}</div>
          <div className="k mono">{computed.formula}</div>
        </div>
      </div>
      {computed.period_cap_reached && (
        <div className="notice warn">{t('capWarning')}</div>
      )}
      {computed.gratuity > 0 && (
        <p className="muted small" style={{ marginTop: -6 }}>
          <span className="mr">{computed.gratuity_words_mr}</span>
          {' · '}{computed.gratuity_words_en}
        </p>
      )}
    </>
  )
}

/**
 * Government resolution references.
 *
 * These are the same on every case until a new circular is issued, so by
 * default they follow the system-wide list and update themselves. Editing one
 * detaches this case from that list; "use the standard list" reattaches it.
 */
function RefsEditor({ refs, auto, onChange, schema, t, notify }) {
  const [busy, setBusy] = useState(false)

  const useDefaults = async () => {
    setBusy(true)
    try {
      const settings = await api.settings()
      onChange(settings.default_refs || [], true)
      notify(t('refsAutoOn'), 'ok')
    } catch (e) {
      notify(e.message, 'err')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="card">
      <h2>
        <BiLabel mr={schema.refs.title_mr} en={schema.refs.title_en} />
        <span className={'badge ' + (auto ? 'auto' : 'ready')}>
          {auto ? t('refsAuto') : t('refsManual')}
        </span>
      </h2>
      <p className="muted small hint">{auto ? t('refsAutoHint') : t('refsManualHint')}</p>
      {refs.map((ref, i) => (
        <div className="row" key={i} style={{ gap: 6, marginBottom: 6, flexWrap: 'nowrap' }}>
          <span className="muted" style={{ minWidth: 20 }}>{i + 1})</span>
          <textarea rows={2} className="mr" value={ref}
            onChange={(e) => onChange(refs.map((r, idx) => (idx === i ? e.target.value : r)))} />
          <button type="button" className="icon danger" title={t('removeRow')}
            onClick={() => onChange(refs.filter((_, idx) => idx !== i))}>🗑</button>
        </div>
      ))}
      <div className="row">
        <button type="button" className="small" onClick={() => onChange([...refs, ''])}>
          + {t('addReference')}
        </button>
        {!auto && (
          <button type="button" className="small" disabled={busy} onClick={useDefaults}>
            ↺ {t('refsUseDefaults')}
          </button>
        )}
      </div>
    </div>
  )
}
