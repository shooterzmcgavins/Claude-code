import { useEffect, useState } from 'react'
import { api } from '../api'
import MarkdownView from '../components/MarkdownView'

export default function Reports() {
  const [reports, setReports] = useState<any[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [content, setContent] = useState('')
  const [search, setSearch] = useState('')

  useEffect(() => {
    api.reports.list().then(setReports).catch(() => {})
  }, [])

  const select = async (taskId: string) => {
    setSelected(taskId)
    try {
      const r = await api.reports.get(taskId)
      setContent(r.content)
    } catch {
      setContent('Failed to load report.')
    }
  }

  const filtered = reports.filter(r =>
    !search || r.task_id.includes(search.toUpperCase()) || r.title?.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="flex h-full">
      {/* List */}
      <div className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col shrink-0">
        <div className="p-3 border-b border-slate-800">
          <h1 className="text-cyan-400 text-xs uppercase tracking-widest mb-2">Reports</h1>
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="search…"
            className="w-full bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded px-2 py-1.5 outline-none focus:border-cyan-700 placeholder-slate-600"
          />
        </div>
        <div className="flex-1 overflow-y-auto divide-y divide-slate-800/50">
          {filtered.map(r => (
            <button
              key={r.task_id}
              onClick={() => select(r.task_id)}
              className={`w-full text-left px-3 py-2 text-xs hover:bg-slate-800 ${selected === r.task_id ? 'bg-slate-800 text-cyan-400' : 'text-slate-400'}`}
            >
              <div className="text-slate-500 font-mono">{r.task_id}</div>
              <div className="truncate">{r.title}</div>
              {r.agent && <div className="text-purple-400">{r.agent}</div>}
            </button>
          ))}
          {filtered.length === 0 && (
            <div className="px-3 py-4 text-slate-600 text-xs">No reports yet</div>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {content ? (
          <MarkdownView content={content} />
        ) : (
          <div className="text-slate-600 text-sm text-center mt-20">Select a report to view</div>
        )}
      </div>
    </div>
  )
}
