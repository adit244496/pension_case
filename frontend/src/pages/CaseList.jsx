import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api'
import ExportMenu from '../components/ExportMenu'
import { useLang, useT } from '../i18n'

export default function CaseList({ notify }) {
  const t = useT()
  const { lang } = useLang()
  const navigate = useNavigate()
  const [cases, setCases] = useState(null)
  const [query, setQuery] = useState('')
  const [busy, setBusy] = useState(false)

  const load = (q = query) =>
    api.listCases(q).then(setCases).catch((e) => notify(e.message, 'err'))

  useEffect(() => { load('') }, [])

  const create = async (copyFrom = null) => {
    setBusy(true)
    try {
      const created = await api.createCase(copyFrom ? { copy_from: copyFrom } : {})
      navigate(`/cases/${created.id}`)
    } catch (e) {
      notify(e.message, 'err')
    } finally {
      setBusy(false)
    }
  }

  const remove = async (item) => {
    if (!window.confirm(t('confirmDelete'))) return
    try {
      await api.deleteCase(item.id)
      notify(`${item.case_no} ${t.pick('हटवले', 'deleted')}`, 'ok')
      load()
    } catch (e) {
      notify(e.message, 'err')
    }
  }

  return (
    <div>
      <div className="row between" style={{ marginBottom: 16 }}>
        <form className="row" onSubmit={(e) => { e.preventDefault(); load() }}>
          <input
            value={query} onChange={(e) => setQuery(e.target.value)}
            placeholder={t('search')} style={{ width: 260 }}
            className={lang === 'mr' ? 'mr' : ''}
          />
          <button type="submit"><span className="ico">🔍</span>{t('search')}</button>
        </form>
        <button className="primary" disabled={busy} onClick={() => create()}>
          <span className="ico">＋</span>{t('newCase')}
        </button>
      </div>

      <div className="card" style={{ padding: 0 }}>
        <table className="data">
          <thead>
            <tr>
              <th style={{ width: 160 }}>{t('caseNo')}</th>
              <th>{t('employee')}</th>
              <th style={{ width: 120 }}>{t('status')}</th>
              <th style={{ width: 150 }}>{t('updated')}</th>
              <th style={{ width: 430 }} className="actions-col">{t('actions')}</th>
            </tr>
          </thead>
          <tbody>
            {cases === null && (
              <tr><td colSpan={5} className="muted">{t('loading')}</td></tr>
            )}
            {cases?.length === 0 && (
              <tr><td colSpan={5} className="muted">{t('nothingHere')}</td></tr>
            )}
            {cases?.map((c) => (
              <tr key={c.id}>
                <td><Link to={`/cases/${c.id}`}>{c.case_no}</Link></td>
                <td>
                  <div className="mr">{c.employee_name_mr || '—'}</div>
                  <div className="muted small">{c.employee_name_en || '—'}</div>
                </td>
                <td>
                  <span className={'badge ' + c.status}>{t(c.status) || c.status}</span>
                  {c.document_count > 0 && (
                    <div className="muted small">
                      {c.document_count} {t('documents')}
                    </div>
                  )}
                </td>
                <td className="small muted">
                  {c.updated_at ? new Date(c.updated_at).toLocaleString() : '—'}
                </td>
                <td className="actions-col">
                  <div className="row-actions-wide">
                    <ExportMenu caseItem={c} notify={notify}
                      onNeedsGenerate={(item) =>
                        navigate(`/cases/${item.id}?tab=documents`)} />
                    <Link className="btn small" to={`/cases/${c.id}`}>
                      <span className="ico">✎</span>{t('edit')}
                    </Link>
                    <button className="small" disabled={busy} onClick={() => create(c.id)}>
                      <span className="ico">⧉</span>{t('duplicate')}
                    </button>
                    <button className="small danger" onClick={() => remove(c)}>
                      <span className="ico">🗑</span>{t('delete')}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
