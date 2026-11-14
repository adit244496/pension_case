import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react'
import * as pdfjs from 'pdfjs-dist'
import workerSrc from 'pdfjs-dist/build/pdf.worker.min.mjs?url'
import { api, apiUrl, auth } from '../api'
import DocumentEditor from './DocumentEditor'
import { useT } from '../i18n'

/**
 * Reads a form without leaving the case, in a window over the page.
 *
 * The pages are drawn by pdf.js rather than handed to the browser's own PDF
 * plugin. An <iframe> depends on whatever the machine has registered for PDFs --
 * on a PC where Acrobat has taken over from Edge's viewer the frame simply comes
 * up blank -- and it gives us no say over how the sheet is presented. Drawing
 * the pages ourselves shows the same thing on every machine and lets the case
 * read the way it prints: white A4 sheets, centred on a grey desk, one under the
 * next, exactly as Word lays out a document in print view.
 */
pdfjs.GlobalWorkerOptions.workerSrc = workerSrc

const NO_PDF = 'no-pdf'
const MIN_SCALE = 0.35
const MAX_SCALE = 3
// A little over life size: the sheet is comfortably readable without the reader
// reaching for the zoom, which is where most people start.
const DEFAULT_SCALE = 1.1
const DESK_PADDING = 56    // the desk's own padding, plus a little slack

/** One page, drawn at the current scale and redrawn when it changes. */
function PdfPage({ pdf, number, scale }) {
  const canvas = useRef(null)

  useEffect(() => {
    let task = null
    let cancelled = false
    pdf.getPage(number).then((page) => {
      if (cancelled || !canvas.current) return
      // Sheets that print landscape carry /Rotate; getViewport honours it, so
      // they arrive upright here just as they do on paper.
      const viewport = page.getViewport({ scale })
      const ratio = window.devicePixelRatio || 1
      const el = canvas.current
      el.width = Math.floor(viewport.width * ratio)
      el.height = Math.floor(viewport.height * ratio)
      el.style.width = `${Math.floor(viewport.width)}px`
      el.style.height = `${Math.floor(viewport.height)}px`
      const ctx = el.getContext('2d')
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0)
      task = page.render({ canvasContext: ctx, viewport })
      task.promise.catch(() => { /* superseded by the next scale */ })
    }).catch(() => { /* the document went away underneath us */ })
    return () => { cancelled = true; if (task) task.cancel() }
  }, [pdf, number, scale])

  return <canvas className="pdf-page" ref={canvas} data-page={number} />
}

export default function DocumentViewer({
  caseId, doc, docs, localDesktop, busy, notify,
  onClose, onSelect, onDownload, onUpload, onReset, onOpenInWord, onAdopt, onSaved,
}) {
  const t = useT()
  const [pdf, setPdf] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [scale, setScale] = useState(DEFAULT_SCALE)
  const [fitting, setFitting] = useState(false)
  const [editing, setEditing] = useState(false)
  const desk = useRef(null)

  /* Fetch and parse. The bearer token rules out a plain <iframe src>, and the
     bytes are needed in the page anyway for pdf.js to read them. */
  useEffect(() => {
    if (!doc?.pdf_path) { setPdf(null); setError(doc ? NO_PDF : ''); return undefined }
    let cancelled = false
    let task = null
    setLoading(true)
    setError('')
    const headers = auth.token ? { Authorization: `Bearer ${auth.token}` } : {}
    // The sheet is addressed by version as well as by id. manual_at moves every
    // time the form is rebuilt, so a Word save that has just been picked up
    // arrives under a URL the browser has never seen and cannot answer from its
    // cache; cache: 'no-cache' then covers the paths that leave it unchanged.
    const version = doc.manual_at || doc.created_at || ''
    const url = `${apiUrl(api.documentPath(caseId, doc.id, 'pdf', true))}`
      + `&v=${encodeURIComponent(version)}`
    fetch(url, { credentials: 'include', headers, cache: 'no-cache' })
      .then((r) => (r.ok ? r.arrayBuffer() : Promise.reject(new Error(r.statusText))))
      .then((buf) => {
        // The loading task, not the document, owns the worker: it is what has
        // to be torn down when another form is opened.
        task = pdfjs.getDocument({ data: buf })
        return task.promise
      })
      .then((parsed) => {
        if (cancelled) return
        setPdf(parsed)
      })
      .catch((e) => { if (!cancelled) setError(e.message || String(e)) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => {
      cancelled = true
      if (task) task.destroy()
    }
    // `t` is deliberately not a dependency: useT() returns a fresh function on
    // every render, so including it would re-run this effect continuously, each
    // pass cancelling the previous fetch and leaving the panel on "loading".
  }, [caseId, doc?.id, doc?.pdf_path, doc?.manual_at])

  /* Fit the sheet to the width of the desk, and keep it fitted while the window
     is resized -- until the reader chooses a zoom of their own. */
  const fitToWidth = useCallback(() => {
    if (!pdf || !desk.current) return
    const width = desk.current.clientWidth - DESK_PADDING
    if (width <= 0) return
    pdf.getPage(1).then((page) => {
      const natural = page.getViewport({ scale: 1 }).width
      const next = Math.min(MAX_SCALE, Math.max(MIN_SCALE, width / natural))
      // Rounded down: rounding up puts the sheet a pixel wider than the desk
      // and the whole page starts scrolling sideways.
      setScale(Math.floor(next * 100) / 100)
    }).catch(() => {})
  }, [pdf])

  useLayoutEffect(() => { if (fitting) fitToWidth() }, [fitting, fitToWidth])

  useEffect(() => {
    if (!fitting) return undefined
    const onResize = () => fitToWidth()
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [fitting, fitToWidth])

  /* Back to the top, and back to reading, when another form is chosen. */
  useEffect(() => {
    if (desk.current) desk.current.scrollTop = 0
    setEditing(false)
  }, [doc?.id])

  const index = docs.findIndex((d) => d.id === doc?.id)
  const step = useCallback((by) => {
    const next = docs[index + by]
    if (next) onSelect(next)
  }, [docs, index, onSelect])

  /* Escape closes, and the arrow keys walk the case, the way a reader expects
     of a window that has taken over the screen. */
  useEffect(() => {
    const onKey = (e) => {
      if (e.target.matches && e.target.matches('input, textarea, select')) return
      if (e.key === 'Escape') { if (!editing) onClose(); return }
      if (editing) return
      if (e.key === 'ArrowLeft') step(-1)
      if (e.key === 'ArrowRight') step(1)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose, step, editing])

  /* The page underneath must not scroll while the window is open. */
  useEffect(() => {
    const previous = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = previous }
  }, [])

  if (!doc) return null

  const zoom = (by) => {
    setFitting(false)
    setScale((s) => Math.min(MAX_SCALE, Math.max(MIN_SCALE, Math.round((s + by) * 100) / 100)))
  }

  return (
    <div className="viewer-overlay" role="dialog" aria-modal="true"
      onMouseDown={(e) => { if (e.target === e.currentTarget && !editing) onClose() }}>
      <div className={`viewer-modal${editing ? ' wide' : ''}`}>
        <header className="viewer-head">
          <button className="icon" title={t('previous')} disabled={index <= 0}
            onClick={() => step(-1)}>‹</button>
          <span className="muted small mono">{index + 1} / {docs.length}</span>
          <button className="icon" title={t('next')} disabled={index >= docs.length - 1}
            onClick={() => step(1)}>›</button>

          <div className="viewer-title">
            <strong>{doc.title_en}</strong>
            <span className="sub mono">{doc.template_code}</span>
            {doc.manual && <span className="badge ready">✎ {t('manualBadge')}</span>}
            {!doc.included && <span className="badge draft">{t('excluded')}</span>}
          </div>

          {editing ? (
            <button onClick={() => setEditing(false)}>
              <span className="ico">👁</span>{t('readMode')}
            </button>
          ) : (
            <>
              <div className="zoom">
                <button className="icon" title={t('zoomOut')} disabled={!pdf}
                  onClick={() => zoom(-0.1)}>−</button>
                <button className="link small" title={t('fitWidth')} disabled={!pdf}
                  onClick={() => setFitting(true)}>{Math.round(scale * 100)}%</button>
                <button className="icon" title={t('zoomIn')} disabled={!pdf}
                  onClick={() => zoom(0.1)}>+</button>
              </div>
              <button className="primary" onClick={() => setEditing(true)}>
                <span className="ico">✎</span>{t('editHere')}
              </button>
            </>
          )}
          <button className="icon" title={t('close')} onClick={onClose}>✕</button>
        </header>

        <div className={`viewer-desk${editing ? ' editing' : ''}`} ref={desk}>
          {editing && (
            <DocumentEditor
              caseId={caseId} doc={doc} busy={busy} notify={notify}
              onCancel={() => setEditing(false)}
              onSaved={(updated) => { setEditing(false); onSaved(updated) }}
            />
          )}
          {!editing && loading && <p className="muted viewer-msg">{t('loading')}</p>}
          {!editing && error && (
            <div className="viewer-msg">
              <div className="notice warn">{error === NO_PDF ? t('noPdfYet') : error}</div>
              {error !== NO_PDF && (
                <p className="muted small">
                  {t('viewerFallback')}{' '}
                  <button className="link small" onClick={() => onDownload(doc, 'pdf')}>
                    {t('openInNewTab')}
                  </button>
                </p>
              )}
            </div>
          )}
          {!editing && pdf && !error && Array.from({ length: pdf.numPages }, (_, i) => (
            <PdfPage key={`${doc.id}-${i}`} pdf={pdf} number={i + 1} scale={scale} />
          ))}
        </div>

        {/* The editor carries its own save and cancel; the file actions would
            only compete with them while an edit is open. */}
        {!editing && (
        <footer className="viewer-actions">
          <button onClick={() => onDownload(doc, 'docx')}>
            <span className="ico">⬇</span>{t('downloadWord')}
          </button>
          {localDesktop && (
            <>
              <button className="primary" onClick={() => onOpenInWord(doc)}
                      disabled={busy}>
                <span className="ico">📝</span>{t('openInWord')}
              </button>
              {/* A save in Word is picked up on its own, so this is only the way
                  back when that cannot happen -- a form whose PDF failed to
                  convert is not adopted automatically, and would otherwise be
                  recoverable only by resetting, which throws the edits away. */}
              <button onClick={() => onAdopt(doc)} disabled={busy}>
                <span className="ico">↻</span>{t('adoptEdits')}
              </button>
            </>
          )}
          <button onClick={() => onUpload(doc)} disabled={busy}>
            <span className="ico">⬆</span>{t('uploadEdited')}
          </button>
          {doc.manual && (
            <button className="danger" onClick={() => onReset(doc)} disabled={busy}>
              <span className="ico">↺</span>{t('resetToGenerated')}
            </button>
          )}
          <div className="spacer" />
          <span className="muted small viewer-hint">
            {localDesktop ? t('editHintDesktop') : t('editHintUpload')}
          </span>
        </footer>
        )}
      </div>
    </div>
  )
}
