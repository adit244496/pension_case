import { useState } from 'react'
import DateInput from './DateInput'
import { BiLabel } from './Field'
import { deriveCell, deriveTotal } from '../compute'
import { useLang, useT } from '../i18n'

const isMarathi = (key) => /(_mr$|_mr_)/.test(key)

/**
 * Fixed column widths in px. The table scrolls sideways rather than squeezing
 * every field: a cramped "Appointment" box is harder to work with than a scroll.
 */
const WIDTH = { textarea: 230, date: 112, number: 92, select: 130, text: 140 }
const NUM_W = 38
const COMPUTED_W = 104
const ACTIONS_W = 124

function Cell({ column, value, onChange, placeholder, warn }) {
  const props = {
    value: value ?? '',
    onChange: (e) => onChange(e.target.value),
    placeholder,
    className: [isMarathi(column.key) ? 'mr' : '', warn ? 'warn' : ''].join(' ').trim() || undefined,
  }
  if (column.type === 'textarea') return <textarea rows={2} {...props} />
  if (column.type === 'date') {
    return <DateInput value={value} onChange={onChange} className={props.className}
      placeholder={placeholder} />
  }
  if (column.type === 'number') return <input type="text" inputMode="decimal" {...props} />
  return <input type="text" {...props} />
}

/**
 * Editor for one repeating table (service history, leave, family, ...).
 *
 * Derived columns are evaluated as you type using the same rules the renderer
 * applies, so the service periods and totals on screen are the ones that will
 * print. Columns that fill themselves in (leave days, ages) stay editable: the
 * computed figure shows as the placeholder, and a typed value that disagrees is
 * flagged rather than overwritten.
 */
export default function TableEditor({ table, rows, onChange, onDate }) {
  const t = useT()
  const { lang } = useLang()
  const [expanded, setExpanded] = useState(null)
  const [showOptional, setShowOptional] = useState(false)
  const list = Array.isArray(rows) ? rows : []
  const optionalCount = (table.columns || []).filter((c) => c.optional).length
  // Rarely-filled columns are kept out of the way until asked for, but a
  // column that already holds something is always shown.
  const columns = (table.columns || []).filter(
    (c) => !c.optional || showOptional || list.some((r) => String(r[c.key] ?? '').trim()))
  const computed = table.computed || []
  const auto = table.auto || []
  const context = { onDate }

  const setRow = (index, patch) =>
    onChange(list.map((row, i) => (i === index ? { ...row, ...patch } : row)))

  const addRow = () => onChange([...list, blankRow(table)])
  const removeRow = (index) => onChange(list.filter((_, i) => i !== index))
  const copyRow = (index) => {
    const next = [...list]
    next.splice(index + 1, 0, { ...list[index] })
    onChange(next)
  }

  const move = (index, delta) => {
    const target = index + delta
    if (target < 0 || target >= list.length) return
    const next = [...list]
    ;[next[index], next[target]] = [next[target], next[index]]
    onChange(next)
  }

  const help = lang === 'mr' ? table.help_mr : table.help_en
  const colCount = 1 + columns.length + computed.length + 1
  const totalWidth = NUM_W + ACTIONS_W + computed.length * COMPUTED_W +
    columns.reduce((sum, c) => sum + (WIDTH[c.type] || WIDTH.text), 0)

  return (
    <section className="card table-card">
      <h2>
        <BiLabel mr={table.title_mr} en={table.title_en} />
        <span className="sub">{list.length} {t('rows')}</span>
        {computed.length > 0 && <span className="badge auto">{t('autoColumn')}</span>}
        {optionalCount > 0 && (
          <button type="button" className="link small"
            onClick={() => setShowOptional(!showOptional)}>
            {showOptional ? t('hideOptional') : `${t('showOptional')} (${optionalCount})`}
          </button>
        )}
      </h2>
      {help && <p className={'muted small hint ' + (lang === 'mr' ? 'mr' : '')}>{help}</p>}

      <div className="table-scroll">
        <table className="data grid-editor" style={{ minWidth: totalWidth }}>
          <colgroup>
            <col style={{ width: NUM_W }} />
            {columns.map((c) => (
              <col key={c.key} style={{ width: WIDTH[c.type] || WIDTH.text }} />
            ))}
            {computed.map((c) => <col key={c.key} style={{ width: COMPUTED_W }} />)}
            <col style={{ width: ACTIONS_W }} />
          </colgroup>
          <thead>
            <tr>
              <th>#</th>
              {columns.map((c) => (
                <th key={c.key} className={c.optional ? 'optional-col' : undefined}>
                  <BiLabel mr={c.label_mr} en={c.label_en} />
                </th>
              ))}
              {computed.map((c) => (
                <th key={c.key} className="computed-head">
                  <BiLabel mr={c.label_mr} en={c.label_en} />
                  <span className="fx">ƒx</span>
                </th>
              ))}
              <th />
            </tr>
          </thead>
          <tbody>
            {list.length === 0 && (
              <tr>
                <td colSpan={colCount} className="muted empty-row">{t('nothingHere')}</td>
              </tr>
            )}
            {list.map((row, i) => (
              <Row
                key={i} index={i} row={row} table={table} columns={columns}
                computed={computed} auto={auto}
                context={context}
                expanded={expanded === i}
                onToggle={() => setExpanded(expanded === i ? null : i)}
                onCell={(key, value) => setRow(i, { [key]: value })}
                onNested={(alternates) => setRow(i, { alternates })}
                onRemove={() => removeRow(i)}
                onCopy={() => copyRow(i)}
                onMove={(d) => move(i, d)}
                t={t}
              />
            ))}
          </tbody>
          {table.total_row && list.length > 0 && (
            <tfoot>
              <tr>
                <td colSpan={1 + columns.length} className="total-label">
                  <BiLabel mr={table.total_row.label_mr} en={table.total_row.label_en} />
                </td>
                <td className="computed-cell total" colSpan={Math.max(computed.length, 1)}>
                  {deriveTotal(table.total_row, list, context) || '—'}
                </td>
                <td />
              </tr>
            </tfoot>
          )}
        </table>
      </div>

      <button type="button" className="small add-row" onClick={addRow}>+ {t('addRow')}</button>
    </section>
  )
}

function Row({ index, row, table, columns, computed, auto, context, expanded, onToggle,
               onCell, onNested, onRemove, onCopy, onMove, t }) {
  const nested = table.nested
  const alternates = Array.isArray(row.alternates) ? row.alternates : []
  const autoFor = (key) => auto.find((a) => a.target === key)

  return (
    <>
      <tr>
        <td className="muted row-no">{index + 1}</td>
        {columns.map((c) => {
          const spec = autoFor(c.key)
          const suggestion = spec ? deriveCell(spec, row, context) : ''
          const typed = String(row[c.key] ?? '').trim()
          const disagrees = !!(suggestion && typed && typed !== suggestion)
          return (
            <td key={c.key}>
              <Cell column={c} value={row[c.key]}
                onChange={(v) => onCell(c.key, v)}
                placeholder={suggestion ? `${t('auto')} ${suggestion}` : undefined}
                warn={disagrees} />
              {disagrees && (
                <div className="cell-note" title={t('autoDiffers')}>
                  ƒx {suggestion}
                </div>
              )}
            </td>
          )
        })}
        {computed.map((c) => {
          const value = deriveCell(c, row, context)
          return (
            <td key={c.key} className="computed-cell">
              {value || <span className="muted">—</span>}
            </td>
          )
        })}
        <td>
          <div className="row-actions">
            <button type="button" className="icon" title={t('moveUp')}
              onClick={() => onMove(-1)}>↑</button>
            <button type="button" className="icon" title={t('moveDown')}
              onClick={() => onMove(1)}>↓</button>
            <button type="button" className="icon" title={t('duplicateRow')}
              onClick={onCopy}>⧉</button>
            <button type="button" className="icon danger" title={t('removeRow')}
              onClick={onRemove}>🗑</button>
          </div>
          {nested && (
            <button type="button" className="link small nested-toggle" onClick={onToggle}>
              {expanded ? '▾' : '▸'} {t('alternates')} ({alternates.length})
            </button>
          )}
        </td>
      </tr>
      {nested && expanded && (
        <tr className="nested-row">
          <td colSpan={2 + columns.length + computed.length}>
            <NestedEditor nested={nested} rows={alternates} onChange={onNested}
              context={context} t={t} />
          </td>
        </tr>
      )}
    </>
  )
}

function NestedEditor({ nested, rows, onChange, context, t }) {
  const auto = nested.auto || []
  const setRow = (index, patch) =>
    onChange(rows.map((row, i) => (i === index ? { ...row, ...patch } : row)))
  return (
    <div className="nested-editor">
      <div className="nested-title">
        <BiLabel mr={nested.title_mr} en={nested.title_en} />
      </div>
      <table className="data grid-editor">
        <thead>
          <tr>
            <th style={{ width: 30 }}>#</th>
            {nested.columns.map((c) => (
              <th key={c.key}><BiLabel mr={c.label_mr} en={c.label_en} /></th>
            ))}
            <th style={{ width: 44 }} />
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 && (
            <tr>
              <td colSpan={nested.columns.length + 2} className="muted empty-row">
                {t('nothingHere')}
              </td>
            </tr>
          )}
          {rows.map((row, i) => (
            <tr key={i}>
              <td className="muted row-no">{i + 1}</td>
              {nested.columns.map((c) => {
                const spec = auto.find((a) => a.target === c.key)
                const suggestion = spec ? deriveCell(spec, row, context) : ''
                return (
                  <td key={c.key}>
                    <Cell column={c} value={row[c.key]}
                      onChange={(v) => setRow(i, { [c.key]: v })}
                      placeholder={suggestion ? `${t('auto')} ${suggestion}` : undefined} />
                  </td>
                )
              })}
              <td>
                <button type="button" className="icon danger" title={t('removeRow')}
                  onClick={() => onChange(rows.filter((_, idx) => idx !== i))}>🗑</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <button type="button" className="small add-row"
        onClick={() => onChange([...rows, blankNested(nested)])}>
        + {t('addRow')}
      </button>
    </div>
  )
}

function blankRow(table) {
  const row = Object.fromEntries(table.columns.map((c) => [c.key, '']))
  if (table.nested) row.alternates = []
  return row
}

function blankNested(nested) {
  return Object.fromEntries(nested.columns.map((c) => [c.key, '']))
}
