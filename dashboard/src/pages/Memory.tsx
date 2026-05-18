import { useEffect, useState } from 'react'
import { api } from '../api'
import MarkdownView from '../components/MarkdownView'

export default function Memory() {
  const [keys, setKeys] = useState<any[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [content, setContent] = useState('')
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState('')
  const [saving, setSaving] = useState(false)

  const loadKeys = () => api.memory.list().then(setKeys).catch(() => {})

  useEffect(() => { loadKeys() }, [])

  const select = async (key: string) => {
    setSelected(key)
    setEditing(false)
    try {
      const r = await api.memory.get(key)
      setContent(r.content)
      setDraft(r.content)
    } catch {
      setContent('')
      setDraft('')
    }
  }

  const save = async () => {
    if (!selected) return
    setSaving(true)
    try {
      await api.memory.write(selected, draft)
      setContent(draft)
      setEditing(false)
      loadKeys()
    } catch {}
    setSaving(false)
  }

  return (
    <div className="flex h-full">
      {/* Keys list */}
      <div className="w-48 bg-slate-900 border-r border-slate-800 flex flex-col shrink-0">
        <div className="p-3 border-b border-slate-800">
          <h1 className="text-cyan-400 text-xs uppercase tracking-widest">Memory</h1>
        </div>
        <div className="flex-1 overflow-y-auto divide-y divide-slate-800/50">
          {keys.map(k => (
            <button
              key={k.key}
              onClick={() => select(k.key)}
              className={`w-full text-left px-3 py-2 text-xs hover:bg-slate-800 ${selected === k.key ? 'bg-slate-800 text-cyan-400' : 'text-slate-400'}`}
            >
              <div>{k.key}</div>
              <div className="text-slate-600">{(k.size / 1024).toFixed(1)}k</div>
            </button>
          ))}
          {keys.length === 0 && (
            <div className="px-3 py-4 text-slate-600 text-xs">No memory entries</div>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {selected && (
          <div className="flex items-center gap-2 px-4 py-2 border-b border-slate-800 bg-slate-900/50 shrink-0">
            <span className="text-slate-400 text-xs font-mono">{selected}.md</span>
            <div className="ml-auto flex gap-2">
              {editing ? (
                <>
                  <button onClick={() => setEditing(false)} className="text-xs text-slate-500 hover:text-slate-300 px-2 py-1">Cancel</button>
                  <button onClick={save} disabled={saving} className="text-xs bg-cyan-800 hover:bg-cyan-700 text-cyan-100 px-3 py-1 rounded disabled:opacity-50">
                    {saving ? 'Saving…' : 'Save'}
                  </button>
                </>
              ) : (
                <button onClick={() => { setEditing(true); setDraft(content) }} className="text-xs text-slate-500 hover:text-slate-300 px-2 py-1 border border-slate-700 rounded">
                  Edit
                </button>
              )}
            </div>
          </div>
        )}

        <div className="flex-1 overflow-auto p-6">
          {!selected ? (
            <div className="text-slate-600 text-sm text-center mt-20">Select a memory key</div>
          ) : editing ? (
            <textarea
              value={draft}
              onChange={e => setDraft(e.target.value)}
              className="w-full h-full bg-slate-900 border border-slate-700 text-slate-200 text-xs font-mono rounded p-4 resize-none outline-none focus:border-cyan-700"
            />
          ) : (
            <MarkdownView content={content} />
          )}
        </div>
      </div>
    </div>
  )
}
