import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { wsClient } from '../ws'
import { WsEvent } from '../types'

const AGENTS = ['builder', 'research', 'planner', 'monitor', 'automation']

type Mode = 'chat' | 'task'

interface Msg {
  id: string
  role: 'user' | 'assistant' | 'tool' | 'system'
  content: string
  agent?: string
  task_id?: string
  ts: string
}

let _msgId = 0
const mkId = () => String(++_msgId)
const now = () => new Date().toISOString()

export default function Chat() {
  const [sessions, setSessions] = useState<any[]>([])
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Msg[]>([])
  const [input, setInput] = useState('')
  const [agent, setAgent] = useState('builder')
  const [mode, setMode] = useState<Mode>('chat')
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null)
  const [sending, setSending] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)

  const push = (m: Omit<Msg, 'id'>) => setMessages(ms => [...ms, { ...m, id: mkId() }])

  useEffect(() => {
    api.chat.sessions().then(setSessions).catch(() => {})
  }, [])

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // WS events — only active in task mode while a task is running
  useEffect(() => {
    const unsub = wsClient.subscribe((e: WsEvent) => {
      if (!activeTaskId || e.task_id !== activeTaskId) return
      if (e.type === 'agent.message' && e.text) {
        push({ role: 'assistant', content: e.text as string, agent: e.agent as string, task_id: e.task_id, ts: e.ts ?? now() })
      }
      if (e.type === 'agent.tool_call') {
        push({ role: 'tool', content: `tool: ${e.tool}(${e.args})`, agent: e.agent as string, task_id: e.task_id, ts: e.ts ?? now() })
      }
      if (e.type === 'approval.pending') {
        push({ role: 'system', content: `Approval needed: ${e.command} — see Approvals page`, ts: now() })
      }
      if (e.type === 'task.complete') {
        setActiveTaskId(null)
        setSending(false)
      }
      if (e.type === 'task.failed') {
        push({ role: 'system', content: 'Task failed', ts: now() })
        setActiveTaskId(null)
        setSending(false)
      }
    })
    return unsub
  }, [activeTaskId])

  const loadSession = async (sid: string) => {
    setSessionId(sid)
    try {
      const data = await api.chat.session(sid)
      setMessages(data.messages.map((m: any) => ({
        id: mkId(),
        role: m.role,
        content: m.content,
        agent: m.agent,
        task_id: m.task_id,
        ts: m.ts,
      })))
    } catch {}
  }

  const newSession = () => {
    setSessionId(null)
    setMessages([])
    setActiveTaskId(null)
    setSending(false)
  }

  // ── CHAT MODE: direct Ollama call, zero task creation ───────────────────────
  const sendDirect = async (text: string) => {
    push({ role: 'user', content: text, ts: now() })
    try {
      const res = await api.chat.direct(text, agent, sessionId ?? undefined)
      setSessionId(res.session_id)
      push({ role: 'assistant', content: res.reply ?? '(no response)', agent: res.agent, ts: now() })
    } catch (err: any) {
      push({ role: 'system', content: `Error: ${err.message}`, ts: now() })
    } finally {
      setSending(false)
    }
    api.chat.sessions().then(setSessions).catch(() => {})
  }

  // ── TASK MODE: task engine, WS events, task tracking ───────────────────────
  const sendTask = async (text: string) => {
    push({ role: 'user', content: text, ts: now() })
    try {
      const res = await api.chat.task(text, agent, sessionId ?? undefined)
      setSessionId(res.session_id)
      setActiveTaskId(res.task_id)
      push({ role: 'system', content: `Task ${res.task_id} → ${res.agent}`, ts: now() })
    } catch (err: any) {
      push({ role: 'system', content: `Error: ${err.message}`, ts: now() })
      setSending(false)
    }
    api.chat.sessions().then(setSessions).catch(() => {})
  }

  const send = async () => {
    const text = input.trim()
    if (!text || sending) return
    setInput('')
    setSending(true)
    if (mode === 'chat') {
      await sendDirect(text)
    } else {
      await sendTask(text)
    }
  }

  const switchMode = (m: Mode) => {
    setMode(m)
    if (m === 'chat') setActiveTaskId(null)
  }

  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
  }

  return (
    <div className="flex h-full">
      {/* Sessions sidebar */}
      <div className="w-48 bg-slate-900 border-r border-slate-800 flex flex-col shrink-0">
        <div className="p-3 border-b border-slate-800 flex items-center justify-between">
          <span className="text-xs text-slate-500 uppercase tracking-widest">Sessions</span>
          <button onClick={newSession} className="text-cyan-400 text-xs hover:text-cyan-300">+ New</button>
        </div>
        <div className="flex-1 overflow-y-auto">
          {sessions.map(s => (
            <button
              key={s.session_id}
              onClick={() => loadSession(s.session_id)}
              className={`w-full text-left px-3 py-2 text-xs border-b border-slate-800/50 hover:bg-slate-800 ${sessionId === s.session_id ? 'bg-slate-800 text-cyan-400' : 'text-slate-400'}`}
            >
              <div className="truncate">{s.preview || s.session_id}</div>
              <div className="text-slate-600 mt-0.5">{s.updated_at?.slice(0, 10)}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Main chat area */}
      <div className="flex flex-col flex-1 overflow-hidden">

        {/* ── Mode toggle bar ── */}
        <div className="flex items-center gap-4 px-4 py-3 border-b-2 border-slate-700 bg-slate-900 shrink-0">
          <span className="text-xs text-slate-400 font-semibold uppercase tracking-widest">Mode:</span>
          <div className="flex items-center bg-slate-800 rounded-md p-1 gap-1">
            <button
              onClick={() => switchMode('chat')}
              className={`px-4 py-1.5 rounded text-xs font-medium transition-colors ${
                mode === 'chat'
                  ? 'bg-cyan-600 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Chat
            </button>
            <button
              onClick={() => switchMode('task')}
              className={`px-4 py-1.5 rounded text-xs font-medium transition-colors ${
                mode === 'task'
                  ? 'bg-purple-700 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Task
            </button>
          </div>

          {/* Agent selector */}
          <span className="text-xs text-slate-500">Agent:</span>
          <select
            value={agent}
            onChange={e => setAgent(e.target.value)}
            className="bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded px-2 py-1 outline-none"
          >
            {AGENTS.map(a => <option key={a} value={a}>{a}</option>)}
          </select>

          {/* Status indicator */}
          <div className="ml-auto text-xs">
            {mode === 'chat' && (
              <span className="text-cyan-500 bg-cyan-950 border border-cyan-800 px-2 py-0.5 rounded">
                Direct reply · no task created
              </span>
            )}
            {mode === 'task' && !activeTaskId && (
              <span className="text-purple-400 bg-purple-950 border border-purple-800 px-2 py-0.5 rounded">
                Task mode · creates tracked job
              </span>
            )}
            {mode === 'task' && activeTaskId && (
              <span className="text-amber-400 bg-amber-950 border border-amber-800 px-2 py-0.5 rounded animate-pulse">
                {activeTaskId} running…
              </span>
            )}
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.length === 0 && (
            <div className="text-slate-600 text-sm text-center mt-20 space-y-2">
              {mode === 'chat' ? (
                <>
                  <div className="text-cyan-700 font-medium">Chat mode</div>
                  <div>Ask anything — direct reply from Ollama, no task created.</div>
                </>
              ) : (
                <>
                  <div className="text-purple-700 font-medium">Task mode</div>
                  <div>Describe a task — routed to an agent, tracked in Tasks.</div>
                </>
              )}
            </div>
          )}
          {messages.map(m => (
            <div key={m.id} className={`flex gap-2 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {m.role !== 'user' && (
                <div className="shrink-0 w-6 h-6 rounded bg-slate-800 flex items-center justify-center text-xs text-cyan-400">
                  {m.agent?.[0]?.toUpperCase() ?? '·'}
                </div>
              )}
              <div className={`max-w-[80%] rounded px-3 py-2 text-xs leading-relaxed ${
                m.role === 'user'   ? 'bg-cyan-950 border border-cyan-800 text-cyan-100 ml-auto' :
                m.role === 'tool'   ? 'bg-slate-900 border border-slate-800 text-amber-300 font-mono' :
                m.role === 'system' ? 'bg-slate-900/50 text-slate-500 italic text-center w-full max-w-full' :
                                      'bg-slate-800 border border-slate-700 text-slate-200'
              }`}>
                {m.role === 'assistant' && m.agent && (
                  <div className="text-purple-400 text-xs mb-1">{m.agent}</div>
                )}
                <div className="whitespace-pre-wrap">{m.content}</div>
                <div className="text-slate-600 text-xs mt-1">{m.ts.slice(11, 19)}</div>
              </div>
            </div>
          ))}
          <div ref={endRef} />
        </div>

        {/* Input — tinted by mode */}
        <div className={`p-3 border-t shrink-0 ${mode === 'chat' ? 'border-cyan-900 bg-cyan-950/20' : 'border-purple-900 bg-purple-950/20'}`}>
          <div className="flex gap-2">
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={onKey}
              placeholder={mode === 'chat' ? 'Ask anything… (Enter to send)' : 'Describe a task… (Enter to send)'}
              rows={2}
              className="flex-1 bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded px-3 py-2 resize-none outline-none focus:border-cyan-700 placeholder-slate-600"
            />
            <button
              onClick={send}
              disabled={sending || !input.trim()}
              className={`px-4 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded text-xs font-medium transition-colors shrink-0 ${
                mode === 'chat'
                  ? 'bg-cyan-700 hover:bg-cyan-600'
                  : 'bg-purple-700 hover:bg-purple-600'
              }`}
            >
              {sending ? '…' : mode === 'chat' ? 'Send' : 'Create Task'}
            </button>
          </div>
          <div className="text-slate-600 text-xs mt-1">Enter to send · Shift+Enter for newline</div>
        </div>
      </div>
    </div>
  )
}
