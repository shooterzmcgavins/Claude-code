import { useEffect, useState } from 'react'
import { api } from '../api'
import { FileEntry } from '../types'

const EDITABLE_EXTS = ['.md', '.txt', '.json', '.yaml', '.yml', '.py', '.sh', '.bat', '.ps1', '.toml', '.env']

export default function Files() {
  const [currentPath, setCurrentPath] = useState('.')
  const [entries, setEntries] = useState<FileEntry[]>([])
  const [selected, setSelected] = useState<FileEntry | null>(null)
  const [content, setContent] = useState('')
  const [draft, setDraft] = useState('')
  const [editing, setEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [pathHistory, setPathHistory] = useState<string[]>(['.'])
  const [newName, setNewName] = useState('')
  const [showNew, setShowNew] = useState(false)

  const listDir = (path: string) => {
    api.files.list(path).then(r => {
      setEntries(r.entries)
      setCurrentPath(path)
    }).catch(() => {})
  }

  useEffect(() => { listDir('.') }, [])

  const openDir = (entry: FileEntry) => {
    setPathHistory(h => [...h, entry.path])
    listDir(entry.path)
    setSelected(null)
    setContent('')
    setEditing(false)
  }

  const goBack = () => {
    const history = [...pathHistory]
    history.pop()
    const prev = history[history.length - 1] || '.'
    setPathHistory(history)
    listDir(prev)
    setSelected(null)
  }

  const openFile = async (entry: FileEntry) => {
    setSelected(entry)
    setEditing(false)
    try {
      const r = await api.files.read(entry.path)
      setContent(r.content)
      setDraft(r.content)
    } catch {
      setContent('Failed to read file.')
    }
  }

  const saveFile = async () => {
    if (!selected) return
    setSaving(true)
    try {
      await api.files.write(selected.path, draft)
      setContent(draft)
      setEditing(false)
    } catch (e: any) {
      alert('Save failed: ' + e.message)
    }
    setSaving(false)
  }

  const deleteEntry = async (entry: FileEntry) => {
    if (!confirm(`Delete ${entry.name}?`)) return
    try {
      await api.files.delete(entry.path)
      listDir(currentPath)
      if (selected?.path === entry.path) { setSelected(null); setContent('') }
    } catch (e: any) {
      alert('Delete failed: ' + e.message)
    }
  }

  const createNew = async (type: 'file' | 'dir') => {
    if (!newName.trim()) return
    const path = currentPath === '.' ? newName : `${currentPath}/${newName}`
    try {
      await api.files.create(path, type)
      setNewName('')
      setShowNew(false)
      listDir(currentPath)
    } catch (e: any) {
      alert('Create failed: ' + e.message)
    }
  }

  const isEditable = (entry: FileEntry | null) => {
    if (!entry || entry.type === 'dir') return false
    return EDITABLE_EXTS.includes(entry.ext) || entry.size < 50000
  }

  const pathParts = currentPath === '.' ? [] : currentPath.split('/')

  return (
    <div className="flex h-full">
      {/* Left: directory browser */}
      <div className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col shrink-0">
        <div className="p-3 border-b border-slate-800 flex items-center gap-2">
          <h1 className="text-cyan-400 text-xs uppercase tracking-widest flex-1">Files</h1>
          <button onClick={() => setShowNew(v => !v)} className="text-xs text-slate-500 hover:text-slate-300 border border-slate-700 px-2 py-0.5 rounded">+</button>
        </div>

        {/* Breadcrumb */}
        <div className="px-3 py-1.5 flex items-center gap-1 text-xs text-slate-600 flex-wrap border-b border-slate-800/50">
          <button onClick={() => { listDir('.'); setPathHistory(['.']) }} className="hover:text-slate-400">workspace</button>
          {pathParts.map((p, i) => (
            <span key={i} className="flex items-center gap-1">
              <span>/</span>
              <button onClick={() => {
                const newPath = pathParts.slice(0, i + 1).join('/')
                listDir(newPath)
                setPathHistory(h => [...h.slice(0, h.findIndex(x => x === newPath) + 1)])
              }} className="hover:text-slate-400">{p}</button>
            </span>
          ))}
        </div>

        {showNew && (
          <div className="p-2 border-b border-slate-800 flex gap-1">
            <input
              value={newName}
              onChange={e => setNewName(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && createNew('file')}
              placeholder="filename.md"
              className="flex-1 bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded px-2 py-1 outline-none"
              autoFocus
            />
            <button onClick={() => createNew('file')} className="text-xs bg-slate-700 hover:bg-slate-600 text-slate-300 px-2 rounded">File</button>
            <button onClick={() => createNew('dir')} className="text-xs bg-slate-700 hover:bg-slate-600 text-slate-300 px-2 rounded">Dir</button>
          </div>
        )}

        {pathHistory.length > 1 && (
          <button onClick={goBack} className="flex items-center gap-2 px-3 py-1.5 text-xs text-slate-600 hover:text-slate-400 hover:bg-slate-800 border-b border-slate-800/50">
            ← back
          </button>
        )}

        <div className="flex-1 overflow-y-auto">
          {entries.map(entry => (
            <div
              key={entry.path}
              className={`flex items-center gap-2 px-3 py-1.5 text-xs cursor-pointer group hover:bg-slate-800 ${selected?.path === entry.path ? 'bg-slate-800 text-cyan-400' : 'text-slate-400'}`}
              onClick={() => entry.type === 'dir' ? openDir(entry) : openFile(entry)}
            >
              <span className="shrink-0 text-slate-600">
                {entry.type === 'dir' ? '▶' : '·'}
              </span>
              <span className="flex-1 truncate">{entry.name}</span>
              {entry.type === 'file' && (
                <span className="text-slate-700 hidden group-hover:block">
                  {(entry.size / 1024).toFixed(1)}k
                </span>
              )}
              <button
                onClick={e => { e.stopPropagation(); deleteEntry(entry) }}
                className="text-red-800 hover:text-red-400 hidden group-hover:block ml-1"
              >×</button>
            </div>
          ))}
          {entries.length === 0 && (
            <div className="px-3 py-4 text-slate-600 text-xs">Empty directory</div>
          )}
        </div>
      </div>

      {/* Right: file viewer/editor */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {selected ? (
          <>
            <div className="flex items-center gap-2 px-4 py-2 border-b border-slate-800 bg-slate-900/50 shrink-0">
              <span className="text-slate-400 text-xs font-mono">{selected.path}</span>
              <div className="ml-auto flex gap-2">
                {isEditable(selected) && (
                  editing ? (
                    <>
                      <button onClick={() => setEditing(false)} className="text-xs text-slate-500 hover:text-slate-300 px-2 py-1">Cancel</button>
                      <button onClick={saveFile} disabled={saving} className="text-xs bg-cyan-800 hover:bg-cyan-700 text-cyan-100 px-3 py-1 rounded disabled:opacity-50">
                        {saving ? 'Saving…' : 'Save'}
                      </button>
                    </>
                  ) : (
                    <button onClick={() => { setEditing(true); setDraft(content) }} className="text-xs text-slate-500 hover:text-slate-300 px-2 py-1 border border-slate-700 rounded">
                      Edit
                    </button>
                  )
                )}
              </div>
            </div>
            <div className="flex-1 overflow-auto p-4">
              {editing ? (
                <textarea
                  value={draft}
                  onChange={e => setDraft(e.target.value)}
                  className="w-full h-full bg-slate-900 border border-slate-700 text-slate-200 text-xs font-mono rounded p-4 resize-none outline-none focus:border-cyan-700"
                />
              ) : (
                <pre className="text-xs text-slate-300 font-mono whitespace-pre-wrap">{content}</pre>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-slate-600 text-sm">
            Select a file to view
          </div>
        )}
      </div>
    </div>
  )
}
