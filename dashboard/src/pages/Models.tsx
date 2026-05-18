import { useEffect, useState } from 'react'
import { api } from '../api'

export default function Models() {
  const [data, setData] = useState<any>(null)

  useEffect(() => { api.models.get().then(setData).catch(() => {}) }, [])

  if (!data) return <div className="p-6 text-slate-600 text-xs">Loading…</div>

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <h1 className="text-cyan-400 text-sm font-bold uppercase tracking-widest">Models</h1>

      <div className="flex gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded p-4 flex-1">
          <div className="text-slate-500 text-xs uppercase tracking-widest mb-1">Provider</div>
          <div className="text-lg font-bold text-slate-200">{data.provider}</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded p-4 flex-1">
          <div className="text-slate-500 text-xs uppercase tracking-widest mb-1">Active Model</div>
          <div className="text-lg font-bold text-cyan-400">{data.active_model}</div>
        </div>
        {data.provider === 'ollama' && (
          <div className="bg-slate-900 border border-slate-800 rounded p-4 flex-1">
            <div className="text-slate-500 text-xs uppercase tracking-widest mb-1">Ollama</div>
            <div className={`text-lg font-bold ${data.ollama_connected ? 'text-emerald-400' : 'text-red-400'}`}>
              {data.ollama_connected ? 'connected' : 'offline'}
            </div>
          </div>
        )}
      </div>

      <div>
        <div className="text-slate-500 text-xs uppercase tracking-widest mb-2">Anthropic Models</div>
        <div className="bg-slate-900 border border-slate-800 rounded overflow-hidden">
          <table className="w-full text-xs">
            <thead className="border-b border-slate-800">
              <tr>
                {['Model ID', 'Name', 'Input $/1M', 'Output $/1M'].map(h => (
                  <th key={h} className="text-left px-4 py-2 text-slate-500 font-normal">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {data.anthropic_models.map((m: any) => (
                <tr key={m.id} className={data.active_model === m.id ? 'bg-cyan-950/30' : ''}>
                  <td className="px-4 py-2 text-slate-400 font-mono">{m.id}</td>
                  <td className="px-4 py-2 text-slate-200">{m.name}</td>
                  <td className="px-4 py-2 text-emerald-400">${m.input_cost}</td>
                  <td className="px-4 py-2 text-amber-400">${m.output_cost}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {data.ollama_models?.length > 0 && (
        <div>
          <div className="text-slate-500 text-xs uppercase tracking-widest mb-2">Local Ollama Models</div>
          <div className="bg-slate-900 border border-slate-800 rounded overflow-hidden">
            <table className="w-full text-xs">
              <thead className="border-b border-slate-800">
                <tr>
                  {['Model', 'Size'].map(h => (
                    <th key={h} className="text-left px-4 py-2 text-slate-500 font-normal">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {data.ollama_models.map((m: any) => (
                  <tr key={m.id} className={data.active_model === m.id ? 'bg-cyan-950/30' : ''}>
                    <td className="px-4 py-2 text-slate-300 font-mono">{m.id}</td>
                    <td className="px-4 py-2 text-slate-500">{m.size ? `${(m.size / 1e9).toFixed(1)}GB` : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
