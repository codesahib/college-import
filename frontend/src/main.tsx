import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './style.css'

type Run = {id:number; filename:string; status:string; total:number; rejected:number; accepted:unknown[]; inserted:number; mapping:string; errors:{row:number;column:string;message:string;value:string}[]}
function App(){
  const [runs,setRuns]=useState<Run[]>([]), [selected,setSelected]=useState<Run|null>(null), [error,setError]=useState('')
  const load=()=>fetch('/api/runs').then(r=>r.json()).then(setRuns)
  useEffect(()=>{load().catch(()=>setError('Backend unavailable on port 8002.'))},[])
  async function upload(file:File){
    setError(''); const body=new FormData();body.append('file',file)
    try {const response=await fetch('/api/imports?workflow=baseline',{method:'POST',body});const result=await response.json();if(!response.ok)throw Error(result.detail);setSelected(result);await load()}catch(e){setError(String(e))}
  }
  return <main><header><span className="brand">◈ FIELDWORK / ENGINEERING LABS</span><span>SYNTHETIC DATA ONLY</span></header><p className="eyebrow">02 / ADMISSIONS OPERATIONS</p><h1>Every row tells a story.<br/><em>Make sure it arrives.</em></h1><p className="intro">Inspect historical admissions imports, trace rejected rows, and maintain a reliable data pipeline.</p><section><h2>Original workflow · strict-v1</h2><p>One known CSV contract. Other vendor schemas need an engineering mapper change.</p><label className="upload">Choose admissions CSV<input type="file" accept=".csv" onChange={e=>{const f=e.target.files?.[0];if(f)void upload(f)}}/></label></section>{error&&<p role="alert">{error}</p>}<section><h2>Import history</h2><table><thead><tr><th>File</th><th>Status</th><th>Accepted</th><th>Rejected</th><th>Mapping</th></tr></thead><tbody>{runs.map(r=><tr key={r.id}><td><button onClick={()=>setSelected(r)}>{r.filename}</button></td><td>{r.status}</td><td>{r.accepted.length}</td><td>{r.rejected}</td><td>{r.mapping}</td></tr>)}</tbody></table>{!runs.length&&<p>No imports yet. Start with fixtures/atlas_v1.csv.</p>}</section>{selected&&<section><h2>{selected.filename} · row report</h2><p>{selected.inserted} inserted / {selected.rejected} rejected</p>{selected.errors.map((e,i)=><p key={i}>Row {e.row} · {e.column}: {e.message} ({e.value})</p>)}</section>}<footer>Independent portfolio demonstration. No real student data or vendor integrations.</footer></main>
}
createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>)
