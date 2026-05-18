import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { wsClient } from '../ws'

function fmtUptime(s: number) {
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60
  return h > 0 ? `${h}h ${m}m` : m > 0 ? `${m}m ${sec}s` : `${sec}s`
}

function StatCard({ label, value, color }: { label: string; value: number | string; color: string }) {
  return (
    <div className={`bg-slate-900 border ${color} rounded p-4`}>
      <div className="text-slate-500 text-xs uppercase tracking-widest mb-1">{label}</div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  )
}

export default function Overview() {
  const [data, setData] = useState<any>(null)
  const [recentEvents, setRecentEvents] = useState<any[]>([])
  const navigate = useNavigate()

  const load = () => {
    api.overview().then(setData).catch(() => {})
    api.events.list(10).then(setRecentEvents).catch(() => {})
  }

  useEffect(() => {
    load()
    const unsub = wsClient.subscribe(e => {
      if (e.type?.startsWith('task.') || e.type === 'event.log') load()
    })
    const iv = setInterval(load, 10000)
    return () => { unsub(); clearInterval(iv) }
  }, [])

  const tc = data?.task_counts ?? {}

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-cyan-400 text-lg font-bold tracking-widest uppercase">Overview</h1>
        {data && (
          <div className="text-xs text-slate-500">
            {data.provider} · {data.model} · uptime {fmtUptime(data.uptime_seconds)}
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard label="Pending" value={tc.pending ?? 0} color="border-slate-700" />
        <StatCard label="Running" value={tc.in_progress ?? 0} color="border-cyan-800" />
        <StatCard label="Complete" value={tc.complete ?? 0} color="border-emerald-800" />
        <StatCard label="Failed" value={tc.failed ?? 0} color="border-red-900" />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <StatCard label="Total Tasks" value={data?.total_tasks ?? 0} color="border-slate-700" />
        <StatCard label="Events Logged" value={data?.event_count ?? 0} color="border-slate-700" />
      </div>

      {/* Recent events */}
      <div>
        <div className="text-xs text-slate-500 uppercase tracking-widest mb-2">Recent Activity</div>
        <div className="bg-slate-900 border border-slate-800 rounded divide-y divide-slate-800">
          {recentEvents.length === 0 && (
            <div className="px-4 py-3 text-slate-600 text-xs">No events yet</div>
          )}
          {recentEvents.map((e, i) => (
            <div key={i} className="flex items-center gap-3 px-4 py-2 text-xs hover:bg-slate-800/40">
              <span className="text-slate-600 shrink-0">{e.ts?.slice(11, 19)}</span>
              <span className={`shrink-0 w-28 ${
                e.type?.includes('complete') ? 'text-emerald-400' :
                e.type?.includes('fail') ? 'text-red-400' :
                e.type?.includes('start') ? 'text-cyan-400' :
                e.type?.includes('approval') ? 'text-amber-400' :
                'text-slate-400'
              }`}>{e.type}</span>
              {e.agent && <span className="text-purple-400 shrink-0">{e.agent}</span>}
              {e.title && <span className="text-slate-300 truncate">{e.title}</span>}
              {e.task_id && (
                <button
                  onClick={() => navigate('/tasks')}
                  className="ml-auto text-slate-600 hover:text-cyan-400 shrink-0"
                >
                  {e.task_id}
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="flex gap-3">
        <button
          onClick={() => navigate('/chat')}
          className="px-4 py-2 bg-cyan-900/50 border border-cyan-700 text-cyan-400 rounded text-xs hover:bg-cyan-900 transition-colors"
        >
          + New Task via Chat
        </button>
        <button
          onClick={() => navigate('/tasks')}
          className="px-4 py-2 bg-slate-800 border border-slate-700 text-slate-300 rounded text-xs hover:bg-slate-700 transition-colors"
        >
          View All Tasks →
        </button>
      </div>
    </div>
  )
}
