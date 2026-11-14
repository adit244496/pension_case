import { useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../api'
import { useT } from '../i18n'

/**
 * Changing the words of a generated form without leaving the app.
 *
 * The forms are ruled tables copied from a printed original, so this does not
 * try to be a word processor: it shows what the sheet says, in the order the
 * sheet says it, and lets the text be changed. Saving writes each change back
 * into the run it came from, which is why the ruling, the merges, the fonts and
 * the page setup are untouched -- and why what comes back is the same document
 * with different words, not a re-creation of it.
 */

/** Rows of cells, so a table on the page looks like a table here. */
function TableGrid({ table, cells, values, onChange }) {
  /* A cell can hold several paragraphs -- the cover sheet is one cell holding
     the whole face of the page -- so they stack inside their cell rather than
     each becoming a column of its own. */
  const rows = []
  for (let r = 0; r < table.rows; r += 1) {
    const byColumn = new Map()
    for (const cell of cells) {
      if (cell.row !== r) continue
      if (!byColumn.has(cell.col)) byColumn.set(cell.col, [])
      byColumn.get(cell.col).push(cell)
    }
    if (!byColumn.size) continue
    const columns = [...byColumn.keys()].sort((a, b) => a - b)
    rows.push({
      r,
      cells: columns.map((col, i) => ({
        col,
        parts: byColumn.get(col),
        // A cell merged across columns leaves a gap before the next one.
        span: (i + 1 < columns.length ? columns[i + 1] : table.cols) - col,
      })),
    })
  }

  return (
    <table className="doc-grid">
      <tbody>
        {rows.map(({ r, cells: rowCells }) => (
          <tr key={r}>
            {rowCells.map(({ col, parts, span }) => (
              <td key={col} colSpan={span > 1 ? span : undefined}>
                {parts.map((part) => {
                  const value = values[part.id] ?? part.text
                  const className = [
                    part.bold ? 'bold' : '',
                    values[part.id] !== undefined ? 'edited' : '',
                  ].filter(Boolean).join(' ') || undefined
                  const style = { textAlign: part.align || undefined }
                  return part.long ? (
                    <textarea key={part.id} rows={2} value={value} title={part.text}
                      className={className} style={style}
                      onChange={(e) => onChange(part, e.target.value)} />
                  ) : (
                    <input key={part.id} value={value} title={part.text}
                      className={className} style={style}
                      onChange={(e) => onChange(part, e.target.value)} />
                  )
                })}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}

export default function DocumentEditor({ caseId, doc, busy, onSaved, onCancel, notify }) {
  const t = useT()
  const [content, setContent] = useState(null)
  const [error, setError] = useState('')
  const [values, setValues] = useState({})
  const [saving, setSaving] = useState(false)
  const first = useRef(null)

  useEffect(() => {
    let cancelled = false
    setContent(null)
    setError('')
    setValues({})
    api.documentContent(caseId, doc.id)
      .then((data) => { if (!cancelled) setContent(data) })
      // A bare "Not found" here means the running server does not have the
      // editing endpoint yet, which a restart fixes -- say so rather than
      // repeating a message that explains nothing.
      .catch((e) => {
        if (cancelled) return
        setError(/^not found$/i.test(e.message) ? t('editorOld') : e.message)
      })
    return () => { cancelled = true }
    // `t` is left out on purpose: useT() is a new function each render.
  }, [caseId, doc.id, doc.manual_at])

  useEffect(() => { if (content && first.current) first.current.focus() }, [content])

  /* Blocks in printed order, with each table's cells kept together. */
  const sections = useMemo(() => {
    if (!content) return []
    const out = []
    let current = null
    for (const block of content.blocks) {
      if (block.kind === 'para') {
        out.push({ type: 'para', block })
        current = null
      } else if (!current || current.key !== block.table) {
        current = { type: 'table', key: block.table, cells: [block] }
        out.push(current)
      } else {
        current.cells.push(block)
      }
    }
    return out
  }, [content])

  const change = (block, text) => {
    setValues((prev) => {
      const next = { ...prev }
      if (text === block.text) delete next[block.id]      // back to how it was
      else next[block.id] = text
      return next
    })
  }

  const changed = Object.keys(values).length

  const save = async () => {
    if (!changed) { onCancel(); return }
    setSaving(true)
    try {
      const edits = Object.entries(values).map(([id, text]) => ({ id, text }))
      const updated = await api.saveDocumentContent(caseId, doc.id, edits)
      notify(t('savedInApp'), 'ok')
      onSaved(updated)
    } catch (e) {
      notify(e.message, 'err')
    } finally {
      setSaving(false)
    }
  }

  const cancel = () => {
    if (changed && !window.confirm(t('discardEdits'))) return
    onCancel()
  }

  return (
    <div className="doc-editor">
      <p className="muted small editor-hint">{t('editorHint')}</p>
      {error && <div className="notice warn">{error}</div>}
      {!content && !error && <p className="muted">{t('loading')}</p>}
      {content && !sections.length && <p className="muted">{t('editorEmpty')}</p>}

      {sections.map((section, index) => section.type === 'para' ? (
        <div key={section.block.id} className="doc-line"
          style={{ textAlign: section.block.align || undefined }}>
          <input
            ref={index === 0 ? first : undefined}
            className={[
              section.block.bold ? 'bold' : '',
              values[section.block.id] !== undefined ? 'edited' : '',
            ].filter(Boolean).join(' ') || undefined}
            style={{ textAlign: section.block.align || undefined }}
            value={values[section.block.id] ?? section.block.text}
            onChange={(e) => change(section.block, e.target.value)} />
        </div>
      ) : (
        <TableGrid key={`${section.key}-${index}`}
          table={content.tables[section.key] || { rows: 0, cols: 0 }}
          cells={section.cells} values={values} onChange={change} />
      ))}

      <div className="editor-bar">
        <button className="primary" onClick={save} disabled={saving || busy}>
          <span className="ico">✔</span>{saving ? t('saving') : t('save')}
        </button>
        <button onClick={cancel} disabled={saving}>{t('cancel')}</button>
        {changed > 0 && (
          <span className="badge draft">{changed} {t('changedCount')}</span>
        )}
      </div>
    </div>
  )
}
