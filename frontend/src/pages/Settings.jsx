import { useEffect, useState } from 'react'
import { api } from '../api'
import { useT } from '../i18n'

/**
 * System-wide defaults.
 *
 * Cases that have not had their references edited follow this list, so a new
 * circular is entered once here rather than on every case.
 */
/**
 * Devanagari faces to type in. Noto Sans Devanagari is Google's Marathi face and
 * is carried with the app, so it is there on every machine and is the default;
 * the rest are whatever Windows or the Linux box already has.
 */
const MR_FONTS = [
  ["'Noto Sans Devanagari'", 'Noto Sans Devanagari'],
  ["'Nirmala UI'", 'Nirmala UI'],
  ["'Mangal'", 'Mangal'],
  ["'Kokila'", 'Kokila'],
  ["'Utsaah'", 'Utsaah'],
  ["'Aparajita'", 'Aparajita'],
  ["'Sanskrit Text'", 'Sanskrit Text'],
  ["'Lohit Devanagari'", 'Lohit Devanagari'],
]

export default function Settings({ notify, user, mrFont, setMrFont }) {
  const t = useT()
  const [refs, setRefs] = useState(null)
  const [saved, setSaved] = useState([])
  const [busy, setBusy] = useState(false)
  const isAdmin = user?.role === 'admin'

  const load = () => api.settings()
    .then((s) => { setRefs(s.default_refs || []); setSaved(s.default_refs || []) })
    .catch((e) => notify(e.message, 'err'))

  useEffect(() => { load() }, [])  // eslint-disable-line react-hooks/exhaustive-deps

  const dirty = JSON.stringify(refs) !== JSON.stringify(saved)

  const save = async () => {
    setBusy(true)
    try {
      const res = await api.saveSetting('default_refs', refs.filter((r) => r.trim()))
      setRefs(res.default_refs); setSaved(res.default_refs)
      notify(t('saved'), 'ok')
    } catch (e) {
      notify(e.message, 'err')
    } finally {
      setBusy(false)
    }
  }

  const restore = async () => {
    setBusy(true)
    try {
      const res = await api.resetSetting('default_refs')
      setRefs(res.default_refs); setSaved(res.default_refs)
      notify(t('saved'), 'ok')
    } catch (e) {
      notify(e.message, 'err')
    } finally {
      setBusy(false)
    }
  }

  if (refs === null) return <p className="muted">{t('loading')}</p>

  return (
    <div style={{ maxWidth: 900 }}>
      <div className="card">
        <h2>{t('mrFont')}</h2>
        <p className="muted small hint">{t('mrFontHint')}</p>
        <div className="grid">
          <label className="field">
            <span className="lbl"><span className="primary">{t('mrFont')}</span></span>
            <select value={mrFont} onChange={(e) => setMrFont(e.target.value)}>
              {MR_FONTS.map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </label>
          <label className="field">
            <span className="lbl"><span className="primary">{t('mrFontPreview')}</span></span>
            <input className="mr" defaultValue="श्री. अण्णासाहेब रंगनाथ कडलग" />
          </label>
        </div>
      </div>

      <div className="card">
        <h2>
          {t('defaultRefs')}
          {dirty && <span className="badge ready">{t('unsaved')}</span>}
        </h2>
        <p className="muted small hint">{t('defaultRefsHint')}</p>

        {refs.map((ref, i) => (
          <div className="row" key={i} style={{ gap: 6, marginBottom: 6, flexWrap: 'nowrap' }}>
            <span className="muted" style={{ minWidth: 20 }}>{i + 1})</span>
            <textarea rows={2} className="mr" value={ref} disabled={!isAdmin}
              onChange={(e) => setRefs(refs.map((r, idx) => (idx === i ? e.target.value : r)))} />
            {isAdmin && (
              <button type="button" className="icon danger" title={t('removeRow')}
                onClick={() => setRefs(refs.filter((_, idx) => idx !== i))}>🗑</button>
            )}
          </div>
        ))}

        {isAdmin && (
          <div className="row" style={{ marginTop: 10 }}>
            <button className="small" onClick={() => setRefs([...refs, ''])}>
              + {t('addReference')}
            </button>
            <div className="spacer" />
            <button className="primary" disabled={busy || !dirty} onClick={save}>
              {busy ? t('saving') : t('save')}
            </button>
            <button className="danger" disabled={busy} onClick={restore}>
              ↺ {t('resetText')}
            </button>
          </div>
        )}
        {!isAdmin && <p className="muted small">{t('adminOnly')}</p>}
      </div>
    </div>
  )
}
