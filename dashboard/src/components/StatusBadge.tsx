import { TaskStatus } from '../types'

const STYLES: Record<string, string> = {
  pending:          'bg-slate-800 text-slate-400 border-slate-700',
  in_progress:      'bg-cyan-950 text-cyan-400 border-cyan-800 animate-pulse',
  needs_approval:   'bg-amber-950 text-amber-400 border-amber-800',
  complete:         'bg-emerald-950 text-emerald-400 border-emerald-800',
  failed:           'bg-red-950 text-red-400 border-red-800',
}

export default function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`inline-block px-2 py-0.5 text-xs rounded border ${STYLES[status] ?? 'bg-slate-800 text-slate-400 border-slate-700'}`}>
      {status.replace('_', ' ')}
    </span>
  )
}
