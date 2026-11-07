import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { api } from './api'
import Review from './Review'
import { fields, labels, statusLabel, type Workflow, type Run, type RecordRow, type Registry } from './models'
import './style.css'

function App() {
  const [workflow, setWorkflow] = useState<Workflow>('improved'),
    [tab, setTab] = useState('imports'),
    [runs, setRuns] = useState<Run[]>([]),
    [records, setRecords] = useState<RecordRow[]>([]),
    [registry, setRegistry] = useState<Registry>({ available: [], approvals: [] }),
    [fixtures, setFixtures] = useState<string[]>([]),
    [sample, setSample] = useState('atlas_v2.csv'),
    [selected, setSelected] = useState<Run | null>(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(''),
    [notice, setNotice] = useState(''),
    [drag, setDrag] = useState(false)
  async function refresh() {
    const [r, s, m, f] = await Promise.all([
      api<Run[]>('/api/runs'),
      api<RecordRow[]>('/api/records'),
      api<Registry>('/api/mappings'),
      api<string[]>('/api/fixtures'),
    ])
    setRuns(r)
    setRecords(s)
    setRegistry(m)
    setFixtures(f)
  }
  useEffect(() => {
    refresh().catch((e) =>
      setError(`Could not reach the service. Start the backend on port 8002. ${e.message}`),
    )
  }, [])
  async function perform(action: () => Promise<Run>) {
    setBusy(true)
    setError('')
    setNotice('')
    try {
      const run = await action()
      setSelected(run)
      setNotice(
        run.replayed
          ? 'Exact file replay: existing run returned. No additional records written.'
          : run.status === 'awaiting_review'
            ? 'Schema held for review. No records written.'
            : `Import processed: ${run.inserted} inserted, ${run.unchanged} unchanged, ${run.rejected} rejected.`,
      )
      await refresh()
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }
  async function upload(file: File) {
    const body = new FormData()
    body.append('file', file)
    await perform(() => api<Run>(`/api/imports?workflow=${workflow}`, { method: 'POST', body }))
  }
  function download(run: Run) {
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(run, null, 2)], { type: 'application/json' }),
    )
    const a = document.createElement('a')
    a.href = url
    a.download = `import-${run.id}-report.json`
    a.click()
    URL.revokeObjectURL(url)
  }
  const visible = runs.filter((r) => r.workflow === workflow),
    count = records.filter((r) => r.workflow === workflow).length,
    held = visible.filter((r) => r.status === 'awaiting_review').length,
    rejected = visible.reduce((s, r) => s + r.rejected, 0),
    drift = visible.filter((r) => r.drift).length
  return (
    <div className="app-shell">
      <aside>
        <a className="brand" href="/">
          ◈{' '}
          <span>
            fieldwork<span className="brand-sub">ENGINEERING LABS</span>
          </span>
        </a>
        <div className="workspace-label">MAINTENANCE WORKSPACE</div>
        <button
          className={tab === 'imports' ? 'nav active' : 'nav'}
          onClick={() => setTab('imports')}
        >
          <span>▤</span> Import workspace <span className="nav-count">02</span>
        </button>
        <button
          className={tab === 'mappings' ? 'nav active' : 'nav'}
          onClick={() => setTab('mappings')}
        >
          <span>⊞</span> Mapping registry
        </button>
        <div className="sidebar-note">
          <span className="live-dot" /> LOCAL DEMONSTRATION
          <p>
            Deterministic imports.
            <br />
            AI-assisted engineering.
          </p>
          <small>
            Independent case study
            <br />
            All records are synthetic.
          </small>
        </div>
      </aside>
      <div className="workspace">
        <header>
          <span>
            Operations <span className="slash">/</span> Admissions data
          </span>
          <div>
            <span className="live-dot" /> Local SQLite <span className="avatar">DO</span>
          </div>
        </header>
        <main>
          <div className="page-title">
            <div>
              <p className="eyebrow">CASE STUDY 02 / DATA RELIABILITY</p>
              <h1>{tab === 'imports' ? 'Admissions imports' : 'Mapping registry'}</h1>
              <p className="subtitle">
                {tab === 'imports'
                  ? 'Keep upstream changes from becoming downstream surprises.'
                  : 'Explicit contracts. Versioned decisions. Repeatable imports.'}
              </p>
            </div>
            <span className="synthetic">◇ Synthetic data only</span>
          </div>
          <div className="comparison">
            <div>
              <strong>One pipeline. Two workflows.</strong>
              <span>Compare the original contract with the maintained importer.</span>
            </div>
            <div className="segmented">
              <button
                className={workflow === 'baseline' ? 'chosen' : ''}
                onClick={() => {
                  setWorkflow('baseline')
                  setSelected(null)
                  setNotice('')
                }}
              >
                Before · strict parser
              </button>
              <button
                className={workflow === 'improved' ? 'chosen' : ''}
                onClick={() => {
                  setWorkflow('improved')
                  setSelected(null)
                  setNotice('')
                }}
              >
                After · safer mappings
              </button>
            </div>
          </div>
          {error && (
            <div className="message error" role="alert">
              {error}
            </div>
          )}
          {notice && (
            <div className="message notice" role="status">
              {notice}
            </div>
          )}
          {tab === 'imports' ? (
            <>
              <div className="stats">
                <div>
                  <span>Records stored</span>
                  <strong data-testid="record-count">
                    {count}
                    <small>unique identities</small>
                  </strong>
                  <p>
                    Baseline {records.filter((r) => r.workflow === 'baseline').length} / Improved{' '}
                    {records.filter((r) => r.workflow === 'improved').length}
                  </p>
                </div>
                <div>
                  <span>Awaiting review</span>
                  <strong className={held ? 'amber-text' : ''}>
                    {held}
                    <small>quarantined schemas</small>
                  </strong>
                  <p>Approval required before any write</p>
                </div>
                <div>
                  <span>Rejected rows</span>
                  <strong>
                    {rejected}
                    <small>across {visible.length} runs</small>
                  </strong>
                  <p>Held rows are counted separately</p>
                </div>
                <div>
                  <span>Schema departures</span>
                  <strong>
                    {drift}
                    <small>noncanonical headers</small>
                  </strong>
                  <p>Visible even when safely normalized</p>
                </div>
              </div>
              <section className="import-panel">
                <div className="section-heading">
                  <div>
                    <h2>Bring your data into focus</h2>
                    <p>
                      {workflow === 'improved'
                        ? 'Known contracts and unique aliases normalize automatically. Ambiguous schemas wait for you.'
                        : 'The original importer accepts applicant_id, year, decision and decision_date headers only.'}
                    </p>
                  </div>
                  <span className="step-number">01 / INGEST</span>
                </div>
                <div className="ingest-grid">
                  <label
                    className={`dropzone ${drag ? 'drag' : ''}`}
                    onDragOver={(e) => {
                      e.preventDefault()
                      setDrag(true)
                    }}
                    onDragLeave={() => setDrag(false)}
                    onDrop={(e) => {
                      e.preventDefault()
                      setDrag(false)
                      if (!busy && e.dataTransfer.files[0]) void upload(e.dataTransfer.files[0])
                    }}
                  >
                    <span className="upload-icon">↥</span>
                    <strong>{busy ? 'Processing import…' : 'Choose a CSV or drop it here'}</strong>
                    <span>UTF-8 · up to 2 MB · 10,000 rows</span>
                    <input
                      aria-label="Upload admissions CSV"
                      type="file"
                      accept=".csv,text/csv"
                      disabled={busy}
                      onChange={(e) => {
                        const file = e.target.files?.[0]
                        e.target.value = ''
                        if (file) void upload(file)
                      }}
                    />
                  </label>
                  <div className="sample-panel">
                    <span className="eyebrow">TRY A REPRODUCIBLE SCENARIO</span>
                    <label htmlFor="sample">Synthetic vendor fixture</label>
                    <select
                      id="sample"
                      value={sample}
                      disabled={busy}
                      onChange={(e) => setSample(e.target.value)}
                    >
                      {fixtures.map((f) => (
                        <option key={f}>{f}</option>
                      ))}
                    </select>
                    <button
                      className="primary"
                      disabled={busy || !fixtures.length}
                      onClick={() =>
                        void perform(async () => {
                          const r = await fetch(`/api/fixtures/${sample}`)
                          if (!r.ok) throw Error('Fixture could not be loaded.')
                          const body = new FormData()
                          body.append('file', new File([await r.blob()], sample))
                          return api<Run>(`/api/imports?workflow=${workflow}`, {
                            method: 'POST',
                            body,
                          })
                        })
                      }
                    >
                      Import sample <span>↗</span>
                    </button>
                    <p>
                      Start with Atlas v2 to see changed headers. Use ambiguous v3 to review a
                      mapping.
                    </p>
                  </div>
                </div>
              </section>
              <section>
                <div className="section-heading">
                  <div>
                    <h2>
                      Import history <span className="count">{visible.length}</span>
                    </h2>
                    <p>Every run keeps its contract, row report, and outcome.</p>
                  </div>
                  <span className="step-number">02 / INSPECT</span>
                </div>
                <div className="table-scroll">
                  <table aria-label="Import history">
                    <thead>
                      <tr>
                        <th>Source file</th>
                        <th>Status</th>
                        <th>Accepted</th>
                        <th>Rejected / held</th>
                        <th>Mapping</th>
                        <th>Schema</th>
                      </tr>
                    </thead>
                    <tbody>
                      {visible.map((r) => (
                        <tr key={r.id} className={selected?.id === r.id ? 'selected' : ''}>
                          <td>
                            <button className="file-link" onClick={() => setSelected(r)}>
                              <span className="file-icon">▤</span>
                              {r.filename}
                            </button>
                            <small className="run-meta">
                              Run #{r.id} · {new Date(r.created_at).toLocaleString()}
                            </small>
                          </td>
                          <td>
                            <span
                              className={`badge ${r.status === 'awaiting_review' ? 'amber' : r.status === 'schema_error' ? 'red' : 'green'}`}
                            >
                              {statusLabel(r.status)}
                            </span>
                          </td>
                          <td>{r.accepted.length}</td>
                          <td>
                            {r.rejected} / {r.held || 0}
                          </td>
                          <td className="mono">{r.mapping || 'Unassigned'}</td>
                          <td>
                            {r.drift ? (
                              <span className="drift">↳ Drift detected</span>
                            ) : (
                              <span className="muted">Original contract</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {!visible.length && (
                  <div className="empty">
                    No imports in this workflow yet. Upload a CSV or import a sample above.
                  </div>
                )}
              </section>
              {selected && (
                <section aria-label="Import detail">
                  <div className="section-heading">
                    <div>
                      <p className="eyebrow">
                        RUN #{selected.id} / {selected.workflow.toUpperCase()}
                      </p>
                      <h2>{selected.filename}</h2>
                      <p>
                        {selected.accepted.length} accepted · {selected.rejected} rejected ·{' '}
                        {selected.held || 0} held · {selected.inserted} inserted ·{' '}
                        {selected.unchanged} unchanged
                      </p>
                    </div>
                    <button onClick={() => download(selected)}>Download report ↓</button>
                  </div>
                  {selected.status === 'awaiting_review' && (
                    <Review
                      key={selected.id}
                      run={selected}
                      busy={busy}
                      onApprove={(body) =>
                        void perform(() =>
                          api<Run>(`/api/runs/${selected.id}/approve`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(body),
                          }),
                        )
                      }
                      onReprocess={() =>
                        void perform(() =>
                          api<Run>(`/api/runs/${selected.id}/reprocess`, { method: 'POST' }),
                        )
                      }
                    />
                  )}
                  <h3>
                    Validation report <span className="count">{selected.errors.length}</span>
                  </h3>
                  {selected.errors.length ? (
                    <div className="table-scroll">
                      <table aria-label="Validation errors">
                        <thead>
                          <tr>
                            <th>CSV row</th>
                            <th>Source column</th>
                            <th>Received</th>
                            <th>Actionable explanation</th>
                          </tr>
                        </thead>
                        <tbody>
                          {selected.errors.map((e, i) => (
                            <tr key={i}>
                              <td>{e.row}</td>
                              <td className="mono">{e.column}</td>
                              <td className="mono">{e.value || '(empty)'}</td>
                              <td>{e.message}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="muted">No validation errors.</p>
                  )}
                  {selected.accepted.length > 0 && (
                    <>
                      <h3>Accepted canonical rows</h3>
                      <div className="table-scroll">
                        <table aria-label="Accepted rows">
                          <thead>
                            <tr>
                              {fields.map((f) => (
                                <th key={f}>{labels[f]}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {selected.accepted.map((r, i) => (
                              <tr key={i}>
                                <td className="mono">{r.applicant_id}</td>
                                <td>{r.year}</td>
                                <td>
                                  <span className="badge neutral">{r.decision}</span>
                                </td>
                                <td>{r.decision_date}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </>
                  )}
                </section>
              )}
            </>
          ) : (
            <>
              <section>
                <div className="section-heading">
                  <div>
                    <h2>Configured & approved contracts</h2>
                    <p>
                      Exact normalized header signatures take priority. Unique aliases use the
                      versioned rules in mappings.json.
                    </p>
                  </div>
                  <span className="badge green">No runtime AI</span>
                </div>
                <div className="mapping-grid">
                  {registry.available.map((m, i) => (
                    <article className="mapping-card" key={i}>
                      <div className="section-heading">
                        <h3>
                          {m.name} <span className="muted">v{m.version}</span>
                        </h3>
                        <span className="badge neutral">{m.source}</span>
                      </div>
                      <p className="mono">{m.date_format}</p>
                      {Object.entries(m.fields).map(([field, source]) => (
                        <div className="mapping-line" key={field}>
                          <span>{field}</span>
                          <span>← {source}</span>
                        </div>
                      ))}
                      <small>Ignored: {m.ignored.join(', ') || 'none'}</small>
                    </article>
                  ))}
                </div>
              </section>
              <section>
                <h2>Operator approval log</h2>
                {registry.approvals.length ? (
                  registry.approvals.map((a, i) => (
                    <p key={i}>
                      {a.name}@{a.version} · {a.reviewer} ·{' '}
                      {new Date(a.created_at).toLocaleString()}
                    </p>
                  ))
                ) : (
                  <p>
                    No operator approvals yet. Review a quarantined import to create a versioned
                    contract.
                  </p>
                )}
              </section>
            </>
          )}
          <footer>
            <span>FIELDWORK / ADMISSIONS IMPORT MAINTENANCE LAB</span>
            <span>Independent synthetic demonstration · No vendor affiliation</span>
          </footer>
        </main>
      </div>
    </div>
  )
}
createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
