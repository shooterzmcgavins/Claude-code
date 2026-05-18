import { useEffect, useState } from 'react'
import { api } from '../api'
import { wsClient } from '../ws'
import { Agent } from '../types'

export default function Agents() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [expanded, setExpanded] = useState<string | null>(null)

  const load = () => api.agents.list().then(setAgents).catch(() => {})

  useEffect(() => {
    load()
    const unsub = wsClient.subscribe(e => {
      if (e.type?.startsWith('task.')) load()
    })
    return unsub
  }, [])

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-4">
      <h1 className="text-cyan-400 text-sm font-bold uppercase tracking-widest mb-4">Agents</h1>

      {agents.map(a => (
        <div key={a.name} className="bg-slate-900 border border-slate-800 rounded overflow-hidden">
          <button
            className="w-full flex items-center gap-4 px-4 py-3 hover:bg-slate-800/40 text-left"
            onClick={() => setExpanded(exp => exp === a.name ? null : a.name)}
          >
            <div className={`w-2 h-2 rounded-full shrink-0 ${a.status === 'active' ? 'bg-cyan-400 animate-pulse' : 'bg-slate-600'}`} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3">
                <span className="text-slate-200 font-bold text-sm">{a.name}</span>
                <span className="text-slate-500 text-xs">{a.role}</span>
                {a.status === 'active' && (
                  <span className="text-cyan-400 text-xs animate-pulse">{a.current_task}</span>
                )}
              </div>
              <div className="text-slate-600 text-xs mt-0.5">
                model: {a.model} · tools: {Array.isArray(a.tools) ? a.tools.join(', ') : a.tools}
              </div>
            </div>
            <div className="text-slate-600 text-xs shrink-0">
              {a.last_activity ? a.last_activity.slice(0, 16).replace('T', ' ') : 'never'}
            </div>
            <span className="text-slate-600 text-xs">{expanded === a.name ? '▲' : '▼'}</span>
          </button>

          {expanded === a.name && (
            <div className="border-t border-slate-800 p-4 space-y-3">
              <div>
                <div className="text-slate-500 text-xs uppercase tracking-widest mb-1">Identity File</div>
                <div className="text-slate-600 text-xs font-mono">{a.source_file || '(built-in fallback)'}</div>
              </div>
              <div>
                <div className="text-slate-500 text-xs uppercase tracking-widest mb-1">Keywords</div>
                <div className="flex flex-wrap gap-1">
                  {a.keywords.map(k => (
                    <span key={k} className="bg-slate-800 text-slate-400 text-xs px-2 py-0.5 rounded">{k}</span>
                  ))}
                </div>
              </div>
              <div>
                <div className="text-slate-500 text-xs uppercase tracking-widest mb-1">System Prompt</div>
                <pre className="bg-slate-950 text-slate-300 text-xs p-3 rounded border border-slate-800 whitespace-pre-wrap overflow-auto max-h-48 leading-relaxed">
                  {a.system_prompt}
                </pre>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
