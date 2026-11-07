import { useState } from 'react'
import { fields, labels, type Run } from './models'

export default function Review({
  run,
  busy,
  onApprove,
  onReprocess,
}: {
  run: Run
  busy: boolean
  onApprove: (body: unknown) => void
  onReprocess: () => void
}) {
  const p = run.proposal!
  const [mapping, setMapping] = useState({ ...p.fields }),
    [name, setName] = useState('Atlas review'),
    [date, setDate] = useState('%Y-%m-%d'),
    [reviewer, setReviewer] = useState('Demo operator'),
    [confirmed, setConfirmed] = useState(false)
  const ignored = p.headers.filter((h) => !Object.values(mapping).includes(h))
  const valid =
    fields.every((f) => mapping[f]) &&
    new Set(Object.values(mapping)).size === 4 &&
    confirmed &&
    name.trim() &&
    reviewer.trim()
  return (
    <div className="review">
      <div className="section-heading">
        <div>
          <p className="eyebrow">HUMAN REVIEW REQUIRED</p>
          <h3>Resolve the schema before importing</h3>
        </div>
        <span className="badge amber">{run.held} rows quarantined</span>
      </div>
      <p>
        No rows have been written. Compare source values, choose the intended application fields,
        and confirm the date contract.
      </p>
      <div className="table-scroll">
        <table aria-label="Source sample">
          <thead>
            <tr>
              {p.headers.map((h) => (
                <th key={h}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {p.sample.map((row, i) => (
              <tr key={i}>
                {p.headers.map((h) => (
                  <td key={h}>{row[h]}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          if (valid) onApprove({ name, fields: mapping, ignored, date_format: date, reviewer })
        }}
      >
        <div className="form-grid">
          {fields.map((field) => (
            <label key={field}>
              {labels[field]}
              <select
                aria-label={labels[field]}
                value={mapping[field]}
                onChange={(e) => {
                  setMapping({ ...mapping, [field]: e.target.value })
                  setConfirmed(false)
                }}
              >
                <option value="">Choose a source column</option>
                {p.headers.map((h) => (
                  <option key={h} value={h}>
                    {h}
                    {p.candidates[field].includes(h) ? ' · candidate' : ''}
                  </option>
                ))}
              </select>
            </label>
          ))}
          <label>
            Date contract
            <select value={date} onChange={(e) => { setDate(e.target.value); setConfirmed(false) }}>
              <option value="%Y-%m-%d">YYYY-MM-DD</option>
              <option value="%m/%d/%Y">MM/DD/YYYY</option>
              <option value="%d.%m.%Y">DD.MM.YYYY</option>
            </select>
          </label>
          <label>
            Mapping name
            <input
              required
              pattern="[A-Za-z][A-Za-z0-9 -]*"
              maxLength={60}
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </label>
          <label>
            Reviewer
            <input
              required
              maxLength={80}
              value={reviewer}
              onChange={(e) => setReviewer(e.target.value)}
            />
          </label>
        </div>
        <label className="confirmation">
          <input
            type="checkbox"
            checked={confirmed}
            onChange={(e) => setConfirmed(e.target.checked)}
          />
          I reviewed the field meanings and date format. Explicitly ignore:{' '}
          {ignored.join(', ') || 'no columns'}.
        </label>
        <div className="actions">
          <button className="primary" disabled={busy || !valid} type="submit">
            Approve mapping & import
          </button>
          <button type="button" disabled={busy} onClick={onReprocess}>
            Retry with approved mappings
          </button>
        </div>
      </form>
    </div>
  )
}
