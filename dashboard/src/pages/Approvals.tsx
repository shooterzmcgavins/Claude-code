import { useEffect, useState } from 'react'
import { api } from '../api'
import { wsClient } from '../ws'
import { ApprovalRequest } from '../types'

interface Props { setPendingApprovals: (fn: (n: number) => number) => void }

export default function Approvals({ setPendingApprovals }: Props) {
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([])
  const [resolved, setResolved] = useState<{id: string, approved: boolean}[]>([])

  const load = () => api.approvals.pending().then(setApprovals).catch(() => {})

  useEffect(() => {
    load()
    const unsub = wsClient.subscribe(e => {
      if (e.type === 'approval.pending') load()
      if (e.type === 'approval.resolved') {
        load()
        setResolved(rs => [...rs.slice(-19), { id: e.approval_id as string, approved: e.approved as boolean }])
      }
    })
    return unsub
  }, [])

  const resolve = async (id: string, approved: boolean) => {
    try {
      await api.approvals.resolve(id, approved)
      setApprovals(as => as.filter(a => a.id !== id))
      setPendingApprovals(n => Math.max(0, n - 1))
    } catch (err: any) {
      alert(`Error: ${err.message}`)
    }
  }

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <h1 className="text-cyan-400 text-sm font-bold uppercase tracking-widest">Approvals</h1>

      {approvals.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded p-8 text-center text-slate-500 text-xs">
          No pending approvals — shell commands will appear here when agents need permission
        </div>
      ) : (
        <div className="space-y-3">
          {approvals.map(a => (
            <div key={a.id} className="bg-slate-900 border border-amber-800/50 rounded p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-amber-400 text-sm">⚠</span>
                  <span className="text-xs text-slate-500">{a.id}</span>
                  <span className="text-xs text-purple-400">from {a.agent}</span>
                  {a.task_id && <span className="text-xs text-cyan-700">{a.task_id}</span>}
                </div>
                <span className="text-xs text-slate-600">{a.created_at.slice(11, 19)}</span>
              </div>
              <pre className="bg-slate-950 border border-slate-800 rounded p-3 text-xs text-amber-300 font-mono mb-4 whitespace-pre-wrap overflow-auto">
                $ {a.command}
              </pre>
              <div className="flex gap-3">
                <button
                  onClick={() => resolve(a.id, true)}
                  className="flex-1 py-2 bg-emerald-900/50 border border-emerald-700 text-emerald-400 rounded text-xs hover:bg-emerald-900 transition-colors"
                >
                  ✓ Approve
                </button>
                <button
                  onClick={() => resolve(a.id, false)}
                  className="flex-1 py-2 bg-red-950/50 border border-red-800 text-red-400 rounded text-xs hover:bg-red-950 transition-colors"
                >
                  ✕ Reject
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {resolved.length > 0 && (
        <div>
          <div className="text-slate-500 text-xs uppercase tracking-widest mb-2">Recently Resolved</div>
          <div className="bg-slate-900 border border-slate-800 rounded divide-y divide-slate-800">
            {[...resolved].reverse().map(r => (
              <div key={r.id} className="flex items-center gap-3 px-4 py-2 text-xs">
                <span className={r.approved ? 'text-emerald-400' : 'text-red-400'}>
                  {r.approved ? '✓ approved' : '✕ rejected'}
                </span>
                <span className="text-slate-600 font-mono">{r.id}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
