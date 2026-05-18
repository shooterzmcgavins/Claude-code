import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { wsClient } from '../ws'
import { WsEvent } from '../types'

const COLOR: Record<string, string> = {
  'task.complete':  'text-emerald-400',
  'task.failed':    'text-red-400',
  'task.started':   'text-cyan-400',
  'task.created':   'text-blue-400',
  'agent.message':  'text-slate-300',
  'agent.tool_call':'text-amber-400',
  'approval.pending':'text-yellow-400',
  'approval.resolved':'text-purple-400',
  'memory.updated': 'text-teal-400',
}

function color(type: string) {
  return COLOR[type] ?? 'text-slate-500'
}

export default function Events() {
  const [events, setEvents] = useState<any[]>([])
  const [paused, setPaused] = useState(false)
  const [filterType, setFilterType] = useState('')
  const [filterAgent, setFilterAgent] = useState('')
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    api.events.list(100).then(es => setEvents([...es].reverse())).catch(() => {})
  }, [])

  useEffect(() => {
    const unsub = wsClient.subscribe((e: WsEvent) => {
      if (e.type === 'event.log' && !paused) {
        setEvents(es => [...es.slice(-499), e])
      }
    })
    return unsub
  }, [paused])

  useEffect(() => {
    if (!paused) endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [events, paused])

  const filtered = events.filter(e =>
    (!filterType || e.type?.includes(filterType)) &&
    (!filterAgent || e.agent === filterAgent)
  )

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 px-4 py-3 border-b border-slate-800 shrink-0">
        <h1 className="text-cyan-400 text-sm font-bold uppercase tracking-widest">Event Stream</h1>
        <input
          value={filterType}
          onChange={e => setFilterType(e.target.value)}
          placeholder="filter type…"
          className="bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded px-2 py-1 outline-none focus:border-cyan-700 placeholder-slate-600 w-36"
        />
        <input
          value={filterAgent}
          onChange={e => setFilterAgent(e.target.value)}
          placeholder="filter agent…"
          className="bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded px-2 py-1 outline-none focus:border-cyan-700 placeholder-slate-600 w-28"
        />
        <button
          onClick={() => setPaused(p => !p)}
          className={`ml-auto text-xs px-3 py-1 rounded border ${paused ? 'border-amber-700 text-amber-400 bg-amber-950' : 'border-slate-700 text-slate-400'}`}
        >
          {paused ? '▶ Resume' : '⏸ Pause'}
        </button>
        <span className="text-slate-600 text-xs">{filtered.length} events</span>
      </div>

      <div className="flex-1 overflow-y-auto font-mono">
        {filtered.map((e, i) => (
          <div key={i} className="flex items-start gap-3 px-4 py-1.5 text-xs border-b border-slate-900 hover:bg-slate-900/40">
            <span className="text-slate-600 shrink-0 w-20">{e.ts?.slice(11, 19)}</span>
            <span className={`shrink-0 w-32 ${color(e.type)}`}>{e.type}</span>
            {e.agent && <span className="text-purple-400 shrink-0 w-16">{e.agent}</span>}
            {e.task_id && <span className="text-cyan-700 shrink-0">{e.task_id}</span>}
            {e.title && <span className="text-slate-400 truncate">{e.title}</span>}
            {e.text && <span className="text-slate-400 truncate">{String(e.text).slice(0, 80)}</span>}
            {e.tool && <span className="text-amber-300">↳ {e.tool}({e.args})</span>}
            {e.command && <span className="text-slate-400">$ {e.command}</span>}
          </div>
        ))}
        <div ref={endRef} />
      </div>
    </div>
  )
}
