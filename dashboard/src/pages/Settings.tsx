import { useEffect, useState } from 'react'
import { api } from '../api'
import { Settings } from '../types'

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null)
  const [form, setForm] = useState<any>({})
  const [apiKey, setApiKey] = useState('')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    api.settings.get().then(s => {
      setSettings(s)
      setForm({
        provider: s.provider,
        ollama_base_url: s.ollama_base_url,
        ollama_model: s.ollama_model,
        max_tokens: s.max_tokens,
      })
    }).catch(() => {})
  }, [])

  const save = async () => {
    setSaving(true)
    const update: any = { ...form }
    if (apiKey) update.anthropic_api_key = apiKey
    try {
      await api.settings.update(update)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
      const updated = await api.settings.get()
      setSettings(updated)
    } catch (e: any) {
      alert('Error saving: ' + e.message)
    }
    setSaving(false)
  }

  const Field = ({ label, children }: { label: string; children: React.ReactNode }) => (
    <div className="flex flex-col gap-1.5">
      <label className="text-xs text-slate-500 uppercase tracking-widest">{label}</label>
      {children}
    </div>
  )

  const Input = ({ value, onChange, placeholder, type = 'text' }: any) => (
    <input
      type={type}
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      className="bg-slate-800 border border-slate-700 text-slate-200 text-sm rounded px-3 py-2 outline-none focus:border-cyan-700"
    />
  )

  if (!settings) return <div className="p-6 text-slate-600 text-xs">Loading…</div>

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-6">
      <h1 className="text-cyan-400 text-sm font-bold uppercase tracking-widest">Settings</h1>

      <div className="bg-slate-900 border border-slate-800 rounded p-5 space-y-5">
        <div className="text-slate-400 text-xs uppercase tracking-widest pb-2 border-b border-slate-800">Provider</div>

        <Field label="Provider">
          <div className="flex gap-3">
            {['ollama', 'anthropic'].map(p => (
              <button
                key={p}
                onClick={() => setForm((f: any) => ({ ...f, provider: p }))}
                className={`flex-1 py-2 rounded border text-sm transition-colors ${
                  form.provider === p
                    ? 'bg-cyan-900/50 border-cyan-600 text-cyan-300'
                    : 'bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-600'
                }`}
              >
                {p}
              </button>
            ))}
          </div>
        </Field>

        {form.provider === 'ollama' && (
          <>
            <Field label="Ollama URL">
              <Input value={form.ollama_base_url} onChange={(v: string) => setForm((f: any) => ({ ...f, ollama_base_url: v }))} placeholder="http://localhost:11434" />
            </Field>
            <Field label="Ollama Model">
              <Input value={form.ollama_model} onChange={(v: string) => setForm((f: any) => ({ ...f, ollama_model: v }))} placeholder="qwen2.5-coder:7b" />
              <div className="text-xs text-slate-600">Recommended: qwen2.5-coder:7b · qwen3:8b · llama3.2:3b</div>
            </Field>
          </>
        )}

        {form.provider === 'anthropic' && (
          <Field label={`Anthropic API Key ${settings.anthropic_api_key_set ? '(set ✓)' : '(not set)'}`}>
            <Input type="password" value={apiKey} onChange={setApiKey} placeholder={settings.anthropic_api_key_set ? '••••••• (leave blank to keep)' : 'sk-ant-...'} />
          </Field>
        )}

        <Field label="Max Tokens">
          <Input value={form.max_tokens} onChange={(v: string) => setForm((f: any) => ({ ...f, max_tokens: parseInt(v) || 4096 }))} placeholder="4096" />
        </Field>
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={save}
          disabled={saving}
          className="px-5 py-2 bg-cyan-800 hover:bg-cyan-700 text-cyan-100 rounded text-sm disabled:opacity-50 transition-colors"
        >
          {saving ? 'Saving…' : saved ? '✓ Saved' : 'Save Settings'}
        </button>
        <div className="text-xs text-slate-600">Settings persist across restarts</div>
      </div>
    </div>
  )
}
