import { useCallback, useEffect, useRef, useState, lazy, Suspense } from 'react'
import { api, auth, download, openInTab } from '../api'
// pdf.js is a heavy dependency and only matters once a form is opened, so the
// reading window is fetched on demand rather than in the first bundle.
const DocumentViewer = lazy(() => import('../components/DocumentViewer'))
import { useT } from '../i18n'

/**
 * Documents tab.
 *
 * The order of the forms and which of them this case uses are per-case settings
 * kept on the case itself, so they survive a rebuild. A form can also be
 * replaced with a Word file edited outside the system; that document is then
 * left alone by later rebuilds and listed in the notes until it is reset.
 */
export default function Documents({ caseId, caseNo, dirty, onSave, notify,
                                    onGenerated, caseState, health }) {
  const t = useT()
  const [docs, setDocs] = useState(null)
  const [busy, setBusy] = useState(false)
  const [exporting, setExporting] = useState('')
  const [savingPrefs, setSavingPrefs] = useState(false)
  const [viewing, setViewing] = useState(null)
  const uploadFor = useRef(null)
  const fileInput = useRef(null)

  // The list as the server last gave it, so a reload can tell which forms Word
  // changed, and the value the server last reported for the case's documents.
  // Refs rather than state: comparing must not itself cause a render.
  const seen = useRef(null)
  const tick = useRef(null)

  const load = useCallback(() => (
    api.documents(caseId)
      .then((list) => {
        const before = seen.current
        seen.current = list
        setDocs(list)
        // Keep the open document showing the freshly rebuilt version.
        setViewing((cur) => (cur ? list.find((d) => d.id === cur.id) || null : null))
        return { list, before }
      })
      .catch((e) => { notify(e.message, 'err'); return null })
  ), [caseId, notify])

  /* Re-read the list, and let the next tick pass without treating this as a
     change: the tab asked for it, so there is nothing here to announce. */
  const refresh = useCallback(() => { tick.current = null; return load() }, [load])

  useEffect(() => { seen.current = null; refresh() }, [refresh])

  /* Word edits come in by themselves.

     The server takes in any form whose Word file has changed on disk -- a
     directory watcher reacts to the save as it happens, and the call below asks
     as well, which covers a machine where the watcher could not start. Either
     way the rebuilt sheet is ready by the time the answer comes back.

     What is left here is noticing, so the tab asks for one short value rather
     than re-reading every form's row, and fetches the list only once that value
     has moved. A form that changed comes back with a new manual_at, which is
     what the toast keys off -- whichever side picked the edit up. */
  const poll = useRef(null)
  // A tick that finds an edit converts the sheet before it answers, which takes
  // about a second. The timer must not start another one on top of that.
  const asking = useRef(false)
  useEffect(() => {
    poll.current = () => {
      if (asking.current) return
      asking.current = true
      api.documentsTick(caseId).then((res) => {
        const known = tick.current
        tick.current = res.tick
        if (known === null || known === res.tick) return undefined
        return load().then((got) => {
          if (!got?.before) return
          const was = new Map(got.before.map((d) => [d.id, d.manual_at || '']))
          const picked = got.list.filter(
            (d) => d.manual_at && was.has(d.id) && was.get(d.id) !== d.manual_at)
          if (picked.length) {
            notify(picked.length === 1
              ? `${t('wordPickedUp')}: ${picked[0].title_en || picked[0].template_code}`
              : `${t('wordPickedUp')} (${picked.length})`, 'ok')
          }
          onGenerated?.()
        })
      }).catch(() => { /* a blip; the next tick tries again */ })
        .finally(() => { asking.current = false })
    }
  })

  useEffect(() => {
    // Cheap enough to simply run while the tab is on screen. That covers the
    // file being opened in Word from anywhere -- this app, Explorer, a
    // recent-files list -- and not only from the button below.
    const fire = () => { if (!document.hidden) poll.current?.() }
    window.addEventListener('focus', fire)
    document.addEventListener('visibilitychange', fire)
    const timer = setInterval(fire, 1200)
    return () => {
      window.removeEventListener('focus', fire)
      document.removeEventListener('visibilitychange', fire)
      clearInterval(timer)
    }
  }, [])

  const savePrefs = async (forms) => {
    setSavingPrefs(true)
    try {
      await api.setFormPreferences(caseId, forms)
      refresh()
      onGenerated?.()
    } catch (e) {
      notify(e.message, 'err')
      refresh()
    } finally {
      setSavingPrefs(false)
    }
  }

  const move = (index, delta) => {
    const target = index + delta
    if (!docs || target < 0 || target >= docs.length) return
    const next = [...docs]
    ;[next[index], next[target]] = [next[target], next[index]]
    setDocs(next)                                 // optimistic, so it feels instant
    savePrefs(next.map((d, i) => ({ code: d.template_code, order: i + 1 })))
  }

  const toggleIncluded = (doc) =>
    savePrefs([{ code: doc.template_code, included: !doc.included }])

  const resetOrder = async () => {
    if (!window.confirm(t('confirmResetForms'))) return
    setSavingPrefs(true)
    try {
      await api.resetFormPreferences(caseId)
      refresh()
      onGenerated?.()
      notify(t('saved'), 'ok')
    } catch (e) {
      notify(e.message, 'err')
    } finally {
      setSavingPrefs(false)
    }
  }

  const generate = async () => {
    if (dirty) {
      const saved = await onSave()
      if (!saved) return
    }
    setBusy(true)
    try {
      const result = await api.generate(caseId, { codes: null, make_pdf: true })
      const failed = result.filter((d) => d.pdf_error)
      notify(
        failed.length
          ? `${result.length - failed.length}/${result.length} ${t.pick('तयार झाले', 'generated')} — ${failed.length} ${t.pick('अयशस्वी', 'failed')}`
          : `${result.length} ${t.pick('कागदपत्रे तयार झाली', 'documents generated')}`,
        failed.length ? 'err' : 'ok')
      refresh()
      onGenerated?.()
    } catch (e) {
      notify(e.message, 'err')
    } finally {
      setBusy(false)
    }
  }

  const runExport = async (kind, action) => {
    setExporting(kind)
    try {
      const path = api.bundlePath(caseId, kind, action === 'open')
      if (action === 'open') await openInTab(path)
      else await download(path, `${caseNo}_complete.${kind}`)
    } catch (e) {
      notify(e.message, 'err')
    } finally {
      setExporting('')
    }
  }

  const openDoc = async (doc, fmt) => {
    try {
      const path = api.documentPath(caseId, doc.id, fmt, fmt === 'pdf')
      if (fmt === 'pdf') await openInTab(path)
      else await download(path, `${doc.template_code}.docx`)
    } catch (e) {
      notify(e.message, 'err')
    }
  }

  const openInWord = async (doc) => {
    setBusy(true)
    try {
      await api.openInWord(caseId, doc.id)
      notify(t('openedInWord'), 'ok')
    } catch (e) {
      notify(e.message, 'err')
    } finally {
      setBusy(false)
    }
  }

  const adoptEdits = async (doc) => {
    setBusy(true)
    try {
      await api.adoptEdits(caseId, doc.id)
      notify(t('manualSaved'), 'ok')
      refresh()
      onGenerated?.()
    } catch (e) {
      notify(e.message, 'err')
    } finally {
      setBusy(false)
    }
  }

  const uploadEdited = async (file) => {
    const doc = uploadFor.current
    if (!file || !doc) return
    setBusy(true)
    try {
      const form = new FormData()
      form.append('file', file)
      const headers = auth.token ? { Authorization: `Bearer ${auth.token}` } : {}
      const res = await fetch(`/api/cases/${caseId}/documents/${doc.id}/upload`,
        { method: 'POST', body: form, credentials: 'include', headers })
      if (!res.ok) throw new Error((await res.json()).detail || res.statusText)
      notify(t('manualSaved'), 'ok')
      refresh()
      onGenerated?.()
    } catch (e) {
      notify(e.message, 'err')
    } finally {
      setBusy(false)
      uploadFor.current = null
      if (fileInput.current) fileInput.current.value = ''
    }
  }

  const resetDoc = async (doc) => {
    if (!doc?.id) return
    if (!window.confirm(`${doc.title_en}\n\n${t('confirmResetDoc')}`)) return
    setBusy(true)
    try {
      await api.resetDocument(caseId, doc.id)
      notify(t('manualReset'), 'ok')
      refresh()
      onGenerated?.()
    } catch (e) {
      notify(e.message, 'err')
    } finally {
      setBusy(false)
    }
  }

  const rebuilding = caseState?.regen_state === 'running'
  const stale = caseState?.documents_stale
  const notes = caseState?.manual_changes || []
  const hasDocs = docs && docs.length > 0
  const includedCount = (docs || []).filter((d) => d.included).length

  return (
    <div>
      {rebuilding && <div className="notice warn">⏳ {t('staleDocs')}</div>}
      {!rebuilding && stale && (
        <div className="notice warn">
          {t('staleDocs')}{' '}
          <button className="small" onClick={generate} disabled={busy}>
            {busy ? t('generating') : t('regenerate')}
          </button>
        </div>
      )}
      {caseState?.regen_state === 'error' && (
        <div className="notice err">
          {t('staleDocsError')} <span className="mono small">{caseState.regen_error}</span>
        </div>
      )}

      {notes.length > 0 && (
        <div className="card notes-card">
          <h2>{t('manualNotes')}<span className="badge ready">{notes.length}</span></h2>
          <p className="muted small hint">{t('manualNotesHint')}</p>
          <ul className="notes">
            {notes.map((n, i) => (
              <li key={i} className={'note ' + n.kind}>
                <span className="note-kind">{t(`noteKind_${n.kind}`)}</span>
                <span className="mr">{n.label_mr}</span>
                <span className="muted small"> · {n.label_en}</span>
                {n.kind === 'document' && (
                  <button className="link small"
                    onClick={() => resetDoc(docs?.find((d) => d.id === n.doc_id))}>
                    ↺ {t('resetToGenerated')}
                  </button>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {viewing && (
        <Suspense fallback={null}>
        <DocumentViewer
          caseId={caseId} doc={viewing} docs={docs || []} busy={busy}
          localDesktop={health?.local_desktop === true}
          notify={notify}
          onClose={() => setViewing(null)}
          onSelect={setViewing}
          onSaved={() => { refresh(); onGenerated?.() }}
          onDownload={openDoc}
          onUpload={(doc) => { uploadFor.current = doc; fileInput.current?.click() }}
          onReset={resetDoc}
          onOpenInWord={openInWord}
          onAdopt={adoptEdits}
        />
        </Suspense>
      )}

      {hasDocs && (
        <div className="card export-card">
          <h2>
            {t('completeCase')}
            <span className="sub">
              {includedCount} / {docs.length} {t('form')} · {t('completeCaseHint')}
            </span>
          </h2>
          <div className="row">
            <button className="primary" disabled={!!exporting}
              onClick={() => runExport('docx', 'download')}>
              {exporting === 'docx' ? t('preparing') : `⬇ ${t('completeWord')}`}
            </button>
            <button className="primary" disabled={!!exporting}
              onClick={() => runExport('pdf', 'download')}>
              {exporting === 'pdf' ? t('preparing') : `⬇ ${t('completePdf')}`}
            </button>
            <button disabled={!!exporting} onClick={() => runExport('pdf', 'open')}>
              {t('viewPdf')}
            </button>
          </div>
          <p className="muted small" style={{ marginTop: 8, marginBottom: 0 }}>
            {t('exportNote')}
          </p>
        </div>
      )}

      <div className="card">
        <h2>
          {t('generate')}
          <span className="sub">{includedCount} / {docs?.length ?? 0} {t('form')}</span>
          {savingPrefs && <span className="muted small">{t('saving')}</span>}
        </h2>
        {dirty && <div className="notice warn">{t('unsaved')}</div>}
        <p className="muted small hint">{t('documentsHint')}</p>
        <div className="row" style={{ marginBottom: 12 }}>
          <button className="primary" onClick={generate} disabled={busy}>
            {busy ? t('generating') : (hasDocs ? t('regenerate') : t('generate'))}
          </button>
          <button className="small" onClick={resetOrder} disabled={savingPrefs}>
            ↺ {t('resetOrder')}
          </button>
          {busy && <span className="muted small">{t('generatingHint')}</span>}
        </div>

        <input ref={fileInput} type="file" accept=".docx" hidden
          onChange={(e) => uploadEdited(e.target.files?.[0])} />

        <div className="table-scroll">
          <table className="data">
            <thead>
              <tr>
                <th style={{ width: 40 }} title={t('includeHint')}>✓</th>
                <th style={{ width: 40 }}>#</th>
                <th>{t('form')}</th>
                <th style={{ width: 110 }}>{t('status')}</th>
                <th style={{ width: 320 }}>{t('actions')}</th>
              </tr>
            </thead>
            <tbody>
              {!docs && <tr><td colSpan={5} className="muted">{t('loading')}</td></tr>}
              {docs?.length === 0 && (
                <tr><td colSpan={5} className="muted">{t('noDocuments')}</td></tr>
              )}
              {docs?.map((doc, index) => (
                <tr key={doc.id} className={doc.included ? undefined : 'excluded-row'}>
                  <td>
                    <input type="checkbox" checked={doc.included} style={{ width: 'auto' }}
                      title={t('includeHint')} onChange={() => toggleIncluded(doc)} />
                  </td>
                  <td className="muted">{index + 1}</td>
                  <td>
                    <button className="link form-link" onClick={() => setViewing(doc)}
                      title={t('viewInApp')}>
                      {doc.title_en}
                    </button>
                    <div className="muted small mono">{doc.template_code}</div>
                  </td>
                  <td>
                    {doc.manual && (
                      <span className="badge ready" title={doc.manual_by}>
                        ✎ {t('manualBadge')}
                      </span>
                    )}
                    {!doc.manual && doc.pdf_error && (
                      <span className="badge err" title={doc.pdf_error}>
                        {t.pick('त्रुटी', 'error')}
                      </span>
                    )}
                    {!doc.manual && !doc.pdf_error && (
                      <span className="badge generated">✓</span>
                    )}
                  </td>
                  <td>
                    <div className="row" style={{ gap: 4, flexWrap: 'nowrap' }}>
                      <button className="icon" title={t('moveUp')} disabled={index === 0}
                        onClick={() => move(index, -1)}>↑</button>
                      <button className="icon" title={t('moveDown')}
                        disabled={index === docs.length - 1}
                        onClick={() => move(index, 1)}>↓</button>
                      {doc.pdf_path && (
                        <button className="small" title={t('viewInApp')}
                          onClick={() => setViewing(doc)}>👁 {t('view')}</button>
                      )}
                      {doc.docx_path && (
                        <button className="small" onClick={() => openDoc(doc, 'docx')}>Word</button>
                      )}
                      <button className="small" title={t('uploadEditedHint')} disabled={busy}
                        onClick={() => { uploadFor.current = doc; fileInput.current?.click() }}>
                        ⬆ {t('uploadEdited')}
                      </button>
                      {doc.manual && (
                        <button className="small danger" disabled={busy}
                          title={t('resetToGenerated')} onClick={() => resetDoc(doc)}>↺</button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {docs?.some((d) => d.pdf_error) && (
          <div className="notice err" style={{ marginTop: 12 }}>
            <strong>{t('pdfFailed')}:</strong>
            <ul style={{ margin: '6px 0 0 18px' }}>
              {docs.filter((d) => d.pdf_error).map((d) => (
                <li key={d.id} className="small mono">{d.template_code}: {d.pdf_error}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}
