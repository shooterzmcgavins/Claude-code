import { useEffect, useState } from 'react'
import { api } from '../api'
import { HealthStatus } from '../types'

export default function Health() {
  const [data, setData] = useState<HealthStatus | null>(null)
  const [loading, setLoading] = useState(true)

  const check = () => {
    setLoading(true)
    api.health.get().then(d => { setData(d); setLoading(false) }).catch(() => setLoading(false))
  }

  useEffect(() => { check() }, [])

  const Check = ({ ok, label, detail }: { ok: boolean; label: string; detail?: string }) => (
    <div className="flex items-start gap-3 py-3 border-b border-slate-800 last:border-0">
      <span className={`mt-0.5 text-sm font-bold ${ok ? 'text-emerald-400' : 'text-red-400'}`}>
        {ok ? '✓' : '✗'}
      </span>
      <div>
        <div className={`text-sm ${ok ? 'text-slate-200' : 'text-red-300'}`}>{label}</div>
        {detail && <div className="text-xs text-slate-500 mt-0.5">{detail}</div>}
      </div>
    </div>
  )

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-cyan-400 text-sm font-bold uppercase tracking-widest">System Health</h1>
        <button onClick={check} className="text-xs text-slate-500 hover:text-slate-300 border border-slate-700 px-3 py-1 rounded">
          Refresh
        </button>
      </div>

      {loading && <div className="text-slate-600 text-xs">Checking…</div>}

      {data && (
        <>
          <div className={`rounded px-4 py-3 text-sm font-bold border ${
            data.status === 'ok'
              ? 'bg-emerald-950/50 border-emerald-800 text-emerald-400'
              : 'bg-red-950/50 border-red-800 text-red-400'
          }`}>
            {data.status === 'ok' ? '✓ All systems ready' : `⚠ ${data.issues.length} issue${data.issues.length !== 1 ? 's' : ''} found`}
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded p-4 space-y-0">
            <Check ok={data.workspace_exists} label="Workspace directory" detail={data.workspace_path} />
            <Check ok={data.provider === 'ollama' ? data.ollama_connected : data.anthropic_key_set}
                   label={data.provider === 'ollama' ? 'Ollama connected' : 'Anthropic API key set'}
                   detail={data.provider === 'ollama' ? `${data.ollama_model}` : undefined} />
            {data.provider === 'ollama' && (
              <Check ok={data.ollama_model_available} label={`Model available: ${data.ollama_model}`}
                     detail={!data.ollama_model_available ? `Run: ollama pull ${data.ollama_model}` : undefined} />
            )}
          </div>

          {data.issues.length > 0 && (
            <div className="bg-slate-900 border border-amber-800/40 rounded p-4 space-y-3">
              <div className="text-amber-400 text-xs font-bold uppercase tracking-widest">Fix Required</div>
              {data.issues.map((issue, i) => (
                <div key={i} className="text-sm text-slate-300 flex gap-2">
                  <span className="text-amber-500 shrink-0">→</span>
                  <span>{issue}</span>
                </div>
              ))}
            </div>
          )}

          <div className="bg-slate-900 border border-slate-800 rounded p-4 space-y-2">
            <div className="text-slate-500 text-xs uppercase tracking-widest mb-3">Runtime Info</div>
            <div className="flex justify-between text-xs">
              <span className="text-slate-500">Provider</span>
              <span className="text-slate-300 font-mono">{data.provider}</span>
            </div>
            {data.provider === 'ollama' && (
              <div className="flex justify-between text-xs">
                <span className="text-slate-500">Active Model</span>
                <span className="text-cyan-400 font-mono">{data.ollama_model}</span>
              </div>
            )}
            <div className="flex justify-between text-xs">
              <span className="text-slate-500">Workspace</span>
              <span className="text-slate-400 font-mono text-right max-w-xs truncate">{data.workspace_path}</span>
            </div>
          </div>

          {data.provider === 'ollama' && !data.ollama_connected && (
            <div className="bg-slate-900 border border-slate-800 rounded p-4 text-xs text-slate-400 space-y-2">
              <div className="font-bold text-slate-300">Quick Ollama Setup</div>
              <div>1. Install Ollama: <span className="text-cyan-400 font-mono">curl -fsSL https://ollama.ai/install.sh | sh</span></div>
              <div>2. Pull a model: <span className="text-cyan-400 font-mono">ollama pull {data.ollama_model}</span></div>
              <div>3. Start Ollama: <span className="text-cyan-400 font-mono">ollama serve</span></div>
              <div>4. Click Refresh above</div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
