import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { wsClient } from '../ws'
import StatusBadge from '../components/StatusBadge'
import { Task } from '../types'

export default function Tasks() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [filter, setFilter] = useState('')
  const [selected, setSelected] = useState<Task | null>(null)
  const navigate = useNavigate()

  const load = () => api.tasks.list().then(setTasks).catch(() => {})

  const handleCancel = async (id: string) => {
    try {
      await api.tasks.cancel(id)
      load()
    } catch (e: any) {
      alert('Cancel failed: ' + e.message)
    }
  }

  const handleRetry = async (id: string) => {
    try {
      const result = await api.tasks.retry(id)
      load()
      navigate('/overview')
    } catch (e: any) {
      alert('Retry failed: ' + e.message)
    }
  }

  const handleArchive = async (id: string) => {
    try {
      await api.tasks.archive(id)
      load()
      setSelected(null)
    } catch (e: any) {
      alert('Archive failed: ' + e.message)
    }
  }

  useEffect(() => {
    load()
    const unsub = wsClient.subscribe(e => {
      if (e.type?.startsWith('task.')) load()
    })
    return unsub
  }, [])

  const filtered = tasks.filter(t =>
    !filter || t.status === filter || t.agent === filter ||
    t.title.toLowerCase().includes(filter.toLowerCase())
  )

  return (
    <div className="flex h-full">
      {/* List */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex items-center gap-3 p-4 border-b border-slate-800 shrink-0 flex-wrap">
          <h1 className="text-cyan-400 text-sm font-bold uppercase tracking-widest">Tasks</h1>
          <div className="flex gap-1 flex-wrap">
            {['', 'pending', 'in_progress', 'needs_approval', 'complete', 'failed', 'archived'].map(s => (
              <button
                key={s}
                onClick={() => setFilter(s)}
                className={`text-xs px-2 py-0.5 rounded border transition-colors ${
                  filter === s
                    ? 'bg-cyan-900/50 border-cyan-700 text-cyan-300'
                    : 'bg-slate-800 border-slate-700 text-slate-500 hover:text-slate-300'
                }`}
              >
                {s || 'all'}
              </button>
            ))}
          </div>
          <input
            value={filter}
            onChange={e => setFilter(e.target.value)}
            placeholder="filter by agent or title…"
            className="ml-auto bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded px-3 py-1.5 outline-none w-52 focus:border-cyan-700 placeholder-slate-600"
          />
        </div>

        <div className="flex-1 overflow-y-auto">
          <table className="w-full text-xs">
            <thead className="sticky top-0 bg-slate-900 border-b border-slate-800">
              <tr>
                {['ID', 'Title', 'Status', 'Agent', 'Created'].map(h => (
                  <th key={h} className="text-left px-4 py-2 text-slate-500 font-normal tracking-widest uppercase">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {filtered.map(t => (
                <tr
                  key={t.id}
                  onClick={() => setSelected(t)}
                  className={`cursor-pointer hover:bg-slate-800/40 ${selected?.id === t.id ? 'bg-slate-800/60' : ''}`}
                >
                  <td className="px-4 py-2 text-cyan-600 font-mono">{t.id}</td>
                  <td className="px-4 py-2 text-slate-300 max-w-xs truncate">{t.title}</td>
                  <td className="px-4 py-2"><StatusBadge status={t.status} /></td>
                  <td className="px-4 py-2 text-purple-400">{t.agent ?? '—'}</td>
                  <td className="px-4 py-2 text-slate-600">{t.created_at?.slice(0, 16).replace('T', ' ')}</td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr><td colSpan={5} className="px-4 py-8 text-center text-slate-600">No tasks</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Detail panel */}
      {selected && (
        <div className="w-80 border-l border-slate-800 bg-slate-900 overflow-y-auto shrink-0">
          <div className="flex items-center justify-between p-4 border-b border-slate-800">
            <span className="text-xs text-cyan-400 font-mono">{selected.id}</span>
            <button onClick={() => setSelected(null)} className="text-slate-600 hover:text-slate-300 text-xs">✕</button>
          </div>
          <div className="p-4 space-y-4 text-xs">
            <div>
              <div className="text-slate-500 mb-1">Title</div>
              <div className="text-slate-200">{selected.title}</div>
            </div>
            <div>
              <div className="text-slate-500 mb-1">Status</div>
              <StatusBadge status={selected.status} />
            </div>
            {selected.agent && (
              <div>
                <div className="text-slate-500 mb-1">Agent</div>
                <div className="text-purple-400">{selected.agent}</div>
              </div>
            )}
            <div>
              <div className="text-slate-500 mb-1">Description</div>
              <div className="text-slate-300 whitespace-pre-wrap leading-relaxed">{selected.description}</div>
            </div>
            {selected.result && (
              <div>
                <div className="text-slate-500 mb-1">Result</div>
                <div className="text-slate-300 whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto">{selected.result}</div>
              </div>
            )}
            {selected.has_report && (
              <a href={`/reports`} className="block text-center py-2 bg-slate-800 border border-slate-700 rounded text-slate-400 hover:text-cyan-400 hover:border-cyan-700 transition-colors">
                View Report →
              </a>
            )}
            <div className="flex gap-2 pt-4 border-t border-slate-800">
              {(selected.status === 'pending' || selected.status === 'in_progress') && (
                <button onClick={() => handleCancel(selected.id)} className="text-xs px-3 py-1.5 bg-red-950/50 border border-red-800 text-red-400 rounded hover:bg-red-950">
                  Cancel
                </button>
              )}
              {(selected.status === 'failed' || selected.status === 'complete') && (
                <button onClick={() => handleRetry(selected.id)} className="text-xs px-3 py-1.5 bg-slate-800 border border-slate-700 text-slate-300 rounded hover:bg-slate-700">
                  Retry
                </button>
              )}
              {(selected.status === 'failed' || selected.status === 'complete') && (
                <button onClick={() => handleArchive(selected.id)} className="text-xs px-3 py-1.5 bg-slate-900 border border-slate-700 text-slate-500 rounded hover:bg-slate-800">
                  Archive
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
