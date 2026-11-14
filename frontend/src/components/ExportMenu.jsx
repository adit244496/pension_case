import { useEffect, useRef, useState } from 'react'
import { api, download, openInTab } from '../api'
import { useT } from '../i18n'

/**
 * Per-case export control.
 *
 * Building the complete file runs a Word conversion, so the menu shows which
 * item is being prepared and stays open until it finishes.
 */
export default function ExportMenu({ caseItem, notify, onNeedsGenerate }) {
  const t = useT()
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState('')
  const ref = useRef(null)

  const ready = (caseItem.document_count || 0) > 0

  useEffect(() => {
    if (!open) return
    const close = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false) }
    const escape = (e) => { if (e.key === 'Escape') setOpen(false) }
    document.addEventListener('mousedown', close)
    document.addEventListener('keydown', escape)
    return () => {
      document.removeEventListener('mousedown', close)
      document.removeEventListener('keydown', escape)
    }
  }, [open])

  const run = async (kind, action) => {
    setBusy(kind + action)
    try {
      const path = api.bundlePath(caseItem.id, kind, action === 'open')
      if (action === 'open') {
        await openInTab(path)
      } else {
        const suffix = kind === 'zip' ? '_all_documents' : '_complete'
        await download(path, `${caseItem.case_no}${suffix}.${kind}`)
      }
      setOpen(false)
    } catch (e) {
      notify(e.message, 'err')
    } finally {
      setBusy('')
    }
  }

  if (!ready) {
    return (
      <button className="small" title={t('exportNotReady')}
        onClick={() => onNeedsGenerate(caseItem)}>
        <span className="ico">⬇</span>{t('download')}
      </button>
    )
  }

  return (
    <div className="menu-wrap" ref={ref}>
      <button className="small primary" onClick={() => setOpen(!open)}
        aria-expanded={open} aria-haspopup="menu">
        <span className="ico">⬇</span>{t('download')} <span className="caret">▾</span>
      </button>
      {open && (
        <div className="menu" role="menu">
          <div className="menu-head">
            {caseItem.case_no} · {caseItem.document_count} {t('form')}
          </div>
          <button role="menuitem" disabled={!!busy}
            onClick={() => run('docx', 'download')}>
            <span className="ico">📄</span>
            {busy === 'docxdownload' ? t('preparing') : t('completeWord')}
          </button>
          <button role="menuitem" disabled={!!busy}
            onClick={() => run('pdf', 'download')}>
            <span className="ico">📕</span>
            {busy === 'pdfdownload' ? t('preparing') : t('completePdf')}
          </button>
          <button role="menuitem" disabled={!!busy}
            onClick={() => run('pdf', 'open')}>
            <span className="ico">👁</span>
            {busy === 'pdfopen' ? t('preparing') : t('viewPdf')}
          </button>
        </div>
      )}
    </div>
  )
}
