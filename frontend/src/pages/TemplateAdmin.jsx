import { useCallback, useEffect, useRef, useState } from 'react'
import { api, download, openInTab } from '../api'
import { useLang, useT } from '../i18n'

/**
 * Template administration.
 *
 * The wording of every form is a set of named text blocks; editing one changes
 * only that sentence, so the printed layout is never at risk. Admins who need a
 * layout change download the .docx, edit it in Word and upload it back. Forms
 * can also be added, removed and reordered here.
 */
export default function TemplateAdmin({ notify, user }) {
  const t = useT()
  const { lang } = useLang()
  const [templates, setTemplates] = useState([])
  const [showArchived, setShowArchived] = useState(false)
  const [current, setCurrent] = useState(null)
  const [draft, setDraft] = useState({})
  const [tab, setTab] = useState('text')
  const [cases, setCases] = useState([])
  const [busy, setBusy] = useState(false)
  const [adding, setAdding] = useState(false)
  const [editingMeta, setEditingMeta] = useState(false)
  const fileInput = useRef(null)
  const isAdmin = user?.role === 'admin'

  const loadList = useCallback(() =>
    api.listTemplates(showArchived).then(setTemplates).catch((e) => notify(e.message, 'err')),
  [notify, showArchived])

  useEffect(() => { loadList() }, [loadList])
  useEffect(() => { api.listCases().then(setCases).catch(() => {}) }, [])

  const select = async (id) => {
    try {
      const detail = await api.getTemplate(id)
      setCurrent(detail)
      setDraft(Object.fromEntries(detail.blocks.map((b) => [b.key, b.value])))
    } catch (e) {
      notify(e.message, 'err')
    }
  }

  useEffect(() => {
    if (!templates.length) return
    if (!current || !templates.some((x) => x.id === current.id)) select(templates[0].id)
  }, [templates]) // eslint-disable-line react-hooks/exhaustive-deps

  const changed = current
    ? current.blocks.filter((b) => draft[b.key] !== b.value).length
    : 0

  const act = async (fn, confirmKey) => {
    if (confirmKey && !window.confirm(t(confirmKey))) return null
    setBusy(true)
    try {
      const detail = await fn()
      if (detail && detail.blocks) {
        setCurrent(detail)
        setDraft(Object.fromEntries(detail.blocks.map((b) => [b.key, b.value])))
      }
      await loadList()
      notify(t('saved'), 'ok')
      return detail
    } catch (e) {
      notify(e.message, 'err')
      return null
    } finally {
      setBusy(false)
    }
  }

  const saveBlocks = () => act(() => api.saveBlocks(current.id,
    Object.entries(draft).map(([key, value]) => ({ key, value }))))

  const move = async (index, delta) => {
    const target = index + delta
    if (target < 0 || target >= templates.length) return
    const ids = templates.map((x) => x.id)
    ;[ids[index], ids[target]] = [ids[target], ids[index]]
    setTemplates(ids.map((id) => templates.find((x) => x.id === id)))
    try {
      await api.reorderTemplates(ids)
      await loadList()
    } catch (e) {
      notify(e.message, 'err')
      loadList()
    }
  }

  const removeTemplate = async (tpl) => {
    const message = tpl.builtin ? t('confirmArchive') : t('confirmDeleteForm')
    if (!window.confirm(`${tpl.title_en}\n\n${message}`)) return
    try {
      await api.deleteTemplate(tpl.id)
      if (current?.id === tpl.id) setCurrent(null)
      await loadList()
      notify(tpl.builtin ? t('formArchived') : t('formDeleted'), 'ok')
    } catch (e) {
      notify(e.message, 'err')
    }
  }

  const preview = async (fmt) => {
    setBusy(true)
    try {
      await openInTab(api.previewPath(current.id, cases[0]?.id, fmt))
    } catch (e) {
      notify(e.message, 'err')
    } finally {
      setBusy(false)
    }
  }

  const grabDocx = async (resolved) => {
    try {
      await download(api.templateDocxPath(current.id, resolved),
        resolved ? `${current.code}_with_wording.docx` : current.docx_name)
    } catch (e) {
      notify(e.message, 'err')
    }
  }

  const upload = async (file) => {
    if (!file) return
    await act(() => api.uploadTemplate(current.id, file))
    if (fileInput.current) fileInput.current.value = ''
  }

  return (
    <div className="split">
      <div>
        <div className="row between" style={{ marginBottom: 8 }}>
          <strong className="small">{templates.length} {t('form')}</strong>
          {isAdmin && (
            <button className="small primary" onClick={() => setAdding(true)}>
              + {t('addForm')}
            </button>
          )}
        </div>
        <label className="row small" style={{ gap: 5, marginBottom: 8 }}>
          <input type="checkbox" checked={showArchived} style={{ width: 'auto' }}
            onChange={(e) => setShowArchived(e.target.checked)} />
          {t('showRemoved')}
        </label>

        <div className="list-group">
          {templates.map((tpl, index) => (
            <div key={tpl.id}
              className={'tpl-row' + (current?.id === tpl.id ? ' on' : '') +
                         (tpl.archived ? ' archived' : '')}>
              <button className="tpl-main" onClick={() => select(tpl.id)}>
                <span className="muted">{tpl.order_no}. </span>
                <span className="mr">{tpl.title_mr}</span>
                <div className="muted small">{tpl.title_en}</div>
                <div className="small">
                  {!tpl.enabled && !tpl.archived &&
                    <span className="badge draft">{t('disabled')}</span>}
                  {tpl.archived && <span className="badge err">{t('removed')}</span>}
                  {!tpl.builtin && <span className="badge ready">{t('custom')}</span>}
                </div>
              </button>
              {isAdmin && (
                <div className="tpl-actions">
                  <button className="icon" title={t('moveUp')} disabled={index === 0}
                    onClick={() => move(index, -1)}>↑</button>
                  <button className="icon" title={t('moveDown')}
                    disabled={index === templates.length - 1}
                    onClick={() => move(index, 1)}>↓</button>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div>
        {adding && (
          <AddForm t={t} onCancel={() => setAdding(false)}
            onCreate={async (payload) => {
              const created = await act(() => api.createTemplate(payload))
              if (created) { setAdding(false); select(created.id); setTab('layout') }
            }} busy={busy} />
        )}

        {!current && !adding && <p className="muted">{t('loading')}</p>}

        {current && (
          <>
            <div className="card">
              <h2>
                <span className="mr">{current.title_mr}</span>
                <span className="sub">{current.title_en}</span>
              </h2>
              <div className="row between">
                <div className="row">
                  <label className="row small" style={{ gap: 5 }}>
                    <input type="checkbox" checked={current.enabled} style={{ width: 'auto' }}
                      disabled={!isAdmin || current.archived}
                      onChange={() => act(() =>
                        api.patchTemplate(current.id, { enabled: !current.enabled }))} />
                    {current.enabled ? t('enabled') : t('disabled')}
                  </label>
                  <span className="muted small mono">
                    {current.code} · v{current.version}
                  </span>
                </div>
                <div className="row">
                  {isAdmin && (
                    <button onClick={() => setEditingMeta(!editingMeta)}>
                      <span className="ico">✎</span>{t('editForm')}
                    </button>
                  )}
                  <button className="primary" disabled={busy} onClick={() => preview('pdf')}>
                    {busy ? t('preparing') : `👁 ${t('previewForm')}`}
                  </button>
                </div>
              </div>
              <p className="muted small" style={{ marginTop: 8, marginBottom: 0 }}>
                {t('previewHint')}
              </p>

              {editingMeta && isAdmin && (
                <FormMeta template={current} t={t} busy={busy}
                  onCancel={() => setEditingMeta(false)}
                  onSave={async (payload) => {
                    const saved = await act(() => api.patchTemplate(current.id, payload))
                    if (saved) setEditingMeta(false)
                  }}
                  onRemove={async () => {
                    await removeTemplate(current)
                    setEditingMeta(false)
                  }} />
              )}
            </div>

            <div className="tabs">
              {[['text', t('editText')], ['layout', t('layout')]].map(([key, label]) => (
                <button key={key} className={tab === key ? 'on' : ''}
                  onClick={() => setTab(key)}>{label}</button>
              ))}
            </div>

            {tab === 'text' && (
              <div className="card">
                <h2>
                  {t('editText')}
                  {changed > 0 && <span className="badge ready">{changed}</span>}
                </h2>
                {current.blocks.length === 0 && <p className="muted">{t('noBlocks')}</p>}
                {current.blocks.length > 0 && (
                  <p className="muted small">{t('editTextHint')}</p>
                )}
                <div className="block-editor">
                  {current.blocks.map((block) => {
                    const isChanged = draft[block.key] !== block.value
                    const isCustom = block.value !== block.default_value
                    const inUse = current.placeholders.includes(`t.${block.key}`)
                    return (
                      <div key={block.key} className={'blk' + (isChanged ? ' changed' : '')}>
                        <div className="row between">
                          <span className="small"><strong>{block.label}</strong></span>
                          <span className="key mono">
                            {'{{ t.' + block.key + ' }}'}
                            {isCustom && <span className="badge ready"
                              style={{ marginLeft: 6 }}>{t('edited')}</span>}
                            {!inUse && <span className="badge draft"
                              style={{ marginLeft: 6 }}>{t('unused')}</span>}
                          </span>
                        </div>
                        {block.multiline
                          ? <textarea className="mr" rows={3} value={draft[block.key] ?? ''}
                              onChange={(e) => setDraft({ ...draft, [block.key]: e.target.value })} />
                          : <input className="mr" value={draft[block.key] ?? ''}
                              onChange={(e) => setDraft({ ...draft, [block.key]: e.target.value })} />}
                      </div>
                    )
                  })}
                </div>
                <div className="sticky-actions">
                  <button className="primary" disabled={busy || changed === 0}
                    onClick={saveBlocks}>{busy ? t('saving') : t('save')}</button>
                  <button className="danger" disabled={busy}
                    onClick={() => act(() => api.resetBlocks(current.id), 'confirmReset')}>
                    {t('resetText')}
                  </button>
                  <span className="muted small">
                    {changed > 0 ? t('unsaved') : t('saved')}
                  </span>
                </div>
              </div>
            )}

            {tab === 'layout' && (
              <>
                <div className="card">
                  <h2>{t('layout')}</h2>
                  <p className="muted small">{t('layoutHint')}</p>
                  <div className="row">
                    <button className="primary" onClick={() => grabDocx(true)}>
                      ⬇ {t('downloadWithWording')}
                    </button>
                    <button onClick={() => grabDocx(false)}>
                      ⬇ {t('downloadRaw')}
                    </button>
                    <button onClick={() => fileInput.current?.click()}
                      disabled={busy || !isAdmin}>
                      ⬆ {t('uploadDocx')}
                    </button>
                    <input ref={fileInput} type="file" accept=".docx" hidden
                      onChange={(e) => upload(e.target.files?.[0])} />
                    {current.builtin && (
                      <button className="danger" disabled={busy || !isAdmin}
                        onClick={() => act(() => api.rebuildTemplate(current.id),
                          'confirmRebuild')}>
                        {t('rebuild')}
                      </button>
                    )}
                  </div>
                  <p className="muted small" style={{ marginTop: 8 }}>
                    <strong>{t('downloadWithWording')}</strong> — {t('downloadWithWordingHint')}
                  </p>
                </div>

                <Placeholders current={current} t={t} lang={lang} />
                <Backups templateId={current.id} t={t}
                  onRestore={(name) => act(() => api.restoreBackup(current.id, name))} />
              </>
            )}
          </>
        )}
      </div>
    </div>
  )
}

/** Rename a form, or take it out of the case. Kept behind the Edit action so a
 *  destructive control is never one stray click away in the list. */
function FormMeta({ template, t, busy, onSave, onCancel, onRemove }) {
  const [titleMr, setTitleMr] = useState(template.title_mr || '')
  const [titleEn, setTitleEn] = useState(template.title_en || '')
  const changed = titleMr !== template.title_mr || titleEn !== template.title_en

  return (
    <div className="form-meta">
      <div className="grid">
        <label className="field">
          <span className="lbl"><span className="primary mr">{t('formTitleMr')}</span></span>
          <input className="mr" value={titleMr} onChange={(e) => setTitleMr(e.target.value)} />
        </label>
        <label className="field">
          <span className="lbl"><span className="primary">{t('formTitleEn')}</span></span>
          <input value={titleEn} onChange={(e) => setTitleEn(e.target.value)} />
        </label>
      </div>
      <div className="row" style={{ marginTop: 10 }}>
        <button className="primary" disabled={busy || !changed}
          onClick={() => onSave({ title_mr: titleMr, title_en: titleEn })}>
          {busy ? t('saving') : t('save')}
        </button>
        <button onClick={onCancel}>{t('cancel')}</button>
        <div className="spacer" />
        {template.archived
          ? <button onClick={() => onRemove()}>↺ {t('restore')}</button>
          : <button className="danger" onClick={onRemove}>
              <span className="ico">🗑</span>{t('removeForm')}
            </button>}
      </div>
      <p className="muted small" style={{ marginBottom: 0 }}>{t('removeFormHint')}</p>
    </div>
  )
}

function AddForm({ t, onCancel, onCreate, busy }) {
  const [titleEn, setTitleEn] = useState('')
  const [titleMr, setTitleMr] = useState('')
  const [language, setLanguage] = useState('en')
  const [file, setFile] = useState(null)

  return (
    <div className="card">
      <h2>{t('addForm')}</h2>
      <div className="grid">
        <label className="field">
          <span className="lbl"><span className="primary">{t('formTitleEn')}</span></span>
          <input value={titleEn} onChange={(e) => setTitleEn(e.target.value)} autoFocus />
        </label>
        <label className="field">
          <span className="lbl"><span className="primary mr">{t('formTitleMr')}</span></span>
          <input className="mr" value={titleMr} onChange={(e) => setTitleMr(e.target.value)} />
        </label>
        <label className="field">
          <span className="lbl"><span className="primary">{t('formLanguage')}</span></span>
          <select value={language} onChange={(e) => setLanguage(e.target.value)}>
            <option value="en">English</option>
            <option value="mr">मराठी</option>
            <option value="both">दोन्ही / Both</option>
          </select>
        </label>
        <label className="field">
          <span className="lbl"><span className="primary">{t('formFile')}</span></span>
          <input type="file" accept=".docx" onChange={(e) => setFile(e.target.files?.[0])} />
        </label>
      </div>
      <p className="muted small">{t('addFormHint')}</p>
      <div className="row">
        <button className="primary" disabled={busy || !titleEn.trim()}
          onClick={() => onCreate({ title_en: titleEn.trim(), title_mr: titleMr.trim(), language, file })}>
          {busy ? t('saving') : t('createForm')}
        </button>
        <button onClick={onCancel}>{t('cancel')}</button>
      </div>
    </div>
  )
}

function Placeholders({ current, t }) {
  const [all, setAll] = useState(null)
  const [open, setOpen] = useState(false)
  useEffect(() => { if (open && !all) api.placeholders().then(setAll).catch(() => {}) },
    [open, all])
  return (
    <div className="card">
      <h2>{t('placeholders')}<span className="sub">{current.placeholders.length}</span></h2>
      <div className="row" style={{ gap: 6 }}>
        {current.placeholders.map((p) => (
          <code key={p} className="chip">{p}</code>
        ))}
      </div>
      <button className="link small" style={{ marginTop: 10 }}
        onClick={() => setOpen(!open)}>
        {open ? t('hideAllPlaceholders') : t('showAllPlaceholders')}
      </button>
      {open && all && (
        <div style={{ marginTop: 10 }}>
          {Object.entries(all.groups).map(([group, keys]) => (
            <div key={group} style={{ marginBottom: 8 }}>
              <div className="small"><strong>{group ? `${group}.` : t('topLevel')}</strong></div>
              <div className="row" style={{ gap: 5 }}>
                {keys.map((k) => (
                  <code key={k} className="chip">{group ? `${group}.${k}` : k}</code>
                ))}
              </div>
            </div>
          ))}
          <div className="small"><strong>{t('filters')}</strong></div>
          <div className="row" style={{ gap: 5 }}>
            {all.filters.map((f) => <code key={f} className="chip">|{f}</code>)}
          </div>
          <p className="muted small" style={{ marginTop: 8 }}>{all.note}</p>
        </div>
      )}
    </div>
  )
}

function Backups({ templateId, onRestore, t }) {
  const [items, setItems] = useState([])
  useEffect(() => { api.backups(templateId).then(setItems).catch(() => setItems([])) },
    [templateId])
  if (!items.length) return null
  return (
    <div className="card">
      <h2>{t('backups')}</h2>
      <table className="data">
        <tbody>
          {items.map((b) => (
            <tr key={b.name}>
              <td className="mono small">{b.name}</td>
              <td className="muted small">{new Date(b.saved_at).toLocaleString()}</td>
              <td style={{ width: 100 }}>
                <button className="small" onClick={() => onRestore(b.name)}>
                  {t('restore')}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
