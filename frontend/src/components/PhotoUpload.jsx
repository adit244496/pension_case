import { useEffect, useRef, useState } from 'react'
import { api, auth } from '../api'
import { useT } from '../i18n'

/**
 * The joint photograph that prints inside the box on the photographs sheet.
 *
 * Uploading is immediate rather than part of the case save, because the image
 * is a file rather than a field; the case revision is bumped on the server so
 * the forms rebuild with it.
 */
export default function PhotoUpload({ caseId, photo, onChanged, notify }) {
  const t = useT()
  const [busy, setBusy] = useState(false)
  const [preview, setPreview] = useState('')
  const input = useRef(null)

  useEffect(() => {
    if (!photo) { setPreview(''); return undefined }
    let url = ''
    let cancelled = false
    const headers = auth.token ? { Authorization: `Bearer ${auth.token}` } : {}
    fetch(`/api/cases/${caseId}/photo`, { credentials: 'include', headers })
      .then((r) => (r.ok ? r.blob() : null))
      .then((blob) => {
        if (!blob || cancelled) return
        url = URL.createObjectURL(blob)
        setPreview(url)
      })
      .catch(() => {})
    return () => { cancelled = true; if (url) URL.revokeObjectURL(url) }
  }, [caseId, photo])

  const upload = async (file) => {
    if (!file) return
    setBusy(true)
    try {
      const form = new FormData()
      form.append('file', file)
      const headers = auth.token ? { Authorization: `Bearer ${auth.token}` } : {}
      const res = await fetch(`/api/cases/${caseId}/photo`,
        { method: 'POST', body: form, credentials: 'include', headers })
      if (!res.ok) throw new Error((await res.json()).detail || res.statusText)
      const body = await res.json()
      notify(t('photoUploaded'), 'ok')
      onChanged(body.photo)
    } catch (e) {
      notify(e.message, 'err')
    } finally {
      setBusy(false)
      if (input.current) input.current.value = ''
    }
  }

  const remove = async () => {
    setBusy(true)
    try {
      const headers = auth.token ? { Authorization: `Bearer ${auth.token}` } : {}
      await fetch(`/api/cases/${caseId}/photo`,
        { method: 'DELETE', credentials: 'include', headers })
      onChanged('')
    } catch (e) {
      notify(e.message, 'err')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="card">
      <h2>{t('photograph')}</h2>
      <p className="muted small hint">{t('photographHint')}</p>
      <div className="row" style={{ alignItems: 'flex-start' }}>
        <div className="photo-box">
          {preview
            ? <img src={preview} alt="" />
            : <span className="muted small">{t('noPhoto')}</span>}
        </div>
        <div>
          <input ref={input} type="file" accept="image/jpeg,image/png" hidden
            onChange={(e) => upload(e.target.files?.[0])} />
          <div className="row">
            <button type="button" disabled={busy} onClick={() => input.current?.click()}>
              <span className="ico">⬆</span>
              {busy ? t('saving') : (photo ? t('replacePhoto') : t('uploadPhoto'))}
            </button>
            {photo && (
              <button type="button" className="danger" disabled={busy} onClick={remove}>
                <span className="ico">🗑</span>{t('removePhoto')}
              </button>
            )}
          </div>
          <p className="muted small" style={{ marginBottom: 0 }}>{t('photoFormats')}</p>
        </div>
      </div>
    </div>
  )
}
