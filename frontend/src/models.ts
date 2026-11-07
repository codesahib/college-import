export type Workflow = 'baseline' | 'improved'
export type RecordRow = {
  applicant_id: string
  year: number
  decision: string
  decision_date: string
  workflow?: Workflow
}
export type Issue = { row: number; column: string; message: string; value: string }
export type Mapping = {
  name: string
  version: number
  fields: { [key: string]: string }
  date_format: string
  source: string
  ignored: string[]
}
export type Proposal = {
  headers: string[]
  fields: { [key: string]: string }
  candidates: { [key: string]: string[] }
  sample: { [key: string]: string }[]
}
export type Run = {
  id: number
  filename: string
  workflow: Workflow
  status: string
  total: number
  rejected: number
  held?: number
  accepted: RecordRow[]
  inserted: number
  unchanged: number
  mapping: string | null
  drift: boolean
  errors: Issue[]
  proposal?: Proposal
  created_at: string
  replayed?: boolean
}
export type Registry = {
  available: Mapping[]
  approvals: { name: string; version: number; reviewer: string; created_at: string }[]
}
export const fields = ['applicant_id', 'year', 'decision', 'decision_date']
export const labels: { [key: string]: string } = {
  applicant_id: 'Applicant ID',
  year: 'Application year',
  decision: 'Decision',
  decision_date: 'Decision date',
}
export const statusLabel = (s: string) =>
  ({ completed: 'Processed', awaiting_review: 'Needs review', schema_error: 'Schema rejected' })[
    s
  ] || s
