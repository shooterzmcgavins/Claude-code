import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { wsClient } from '../ws'
import { WsEvent } from '../types'

const ALL_AGENTS = ['supervisor', 'builder', 'research', 'planner', 'monitor', 'automation']

type Mode = 'chat' | 'task'

interface Msg {
  id: string
  role: 'user' | 'assistant' | 'tool' | 'system'
  content: string
  agent?: string
  task_id?: string
  ts: string
}

interface AgentInfo {
  agent: string
  role: string
  identity_file: string
  message_count: number
  last_ts: string
  provider?: string
  model?: string
}

let _msgId = 0
const mkId = () => String(++_msgId)
const now = () => new Date().toISOString()

export default function Chat() {
  const [agent, setAgent] = useState('supervisor')
  const [agentInfoMap, setAgentInfoMap] = useState<Record<string, AgentInfo>>({})
  const [messages, setMessages] = useState<Msg[]>([])
  const [input, setInput] = useState('')
  const [mode, setMode] = useState<Mode>('chat')
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null)
  const [sending, setSending] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const endRef = useRef<HTMLDivElement>(null)

  const push = (m: Omit<Msg, 'id'>) => setMessages(ms => [...ms, { ...m, id: mkId() }])

  const currentAgent = agentInfoMap[agent]

  // Load all agent summaries for sidebar
  useEffect(() => {
    api.chat.agentList().then(list => {
      const map: Record<string, AgentInfo> = {}
      for (const a of list) {
        map[a.agent] = { ...a, identity_file: '', provider: '', model: '' }
      }
      setAgentInfoMap(prev => ({ ...prev, ...map }))
    }).catch(() => {})
  }, [])

  // Load conversation when agent changes
  useEffect(() => {
    api.chat.agentChat(agent).then(data => {
      setMessages(data.messages.map((m: any) => ({
        id: mkId(),
        role: m.role,
        content: m.content,
        agent: m.agent,
        task_id: m.task_id,
        ts: m.ts,
      })))
      setAgentInfoMap(prev => ({
        ...prev,
        [agent]: {
          agent,
          role: data.role,
          identity_file: data.identity_file,
          message_count: data.message_count,
          last_ts: '',
          provider: prev[agent]?.provider ?? '',
          model: prev[agent]?.model ?? '',
        },
      }))
    }).catch(() => {})
  }, [agent])

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // WS — only active in task mode
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
      if (e.type === 'task.complete') { setActiveTaskId(null); setSending(false) }
      if (e.type === 'task.failed') {
        push({ role: 'system', content: 'Task failed', ts: now() })
        setActiveTaskId(null); setSending(false)
      }
    })
    return unsub
  }, [activeTaskId])

  const switchAgent = (name: string) => {
    if (sending) return
    setAgent(name)
    setActiveTaskId(null)
    setMessages([])
  }

  const switchMode = (m: Mode) => {
    setMode(m)
    if (m === 'chat') setActiveTaskId(null)
  }

  const sendDirect = async (text: string) => {
    push({ role: 'user', content: text, ts: now() })
    try {
      const res = await api.chat.direct(text, agent)
      push({ role: 'assistant', content: res.reply ?? '(no response)', agent: res.agent, ts: now() })
      // Update agent info from response
      setAgentInfoMap(prev => ({
        ...prev,
        [agent]: {
          ...prev[agent],
          role: res.agent_role,
          identity_file: res.identity_file,
          provider: res.provider,
          model: res.model,
          message_count: (prev[agent]?.message_count ?? 0) + 2,
        },
      }))
    } catch (err: any) {
      push({ role: 'system', content: `Error: ${err.message}`, ts: now() })
    } finally {
      setSending(false)
    }
  }

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
  }

  const send = async () => {
    const text = input.trim()
    if (!text || sending) return
    setInput('')
    setSending(true)
    if (mode === 'chat') await sendDirect(text)
    else await sendTask(text)
  }

  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
  }

  return (
    <div className="flex h-full">

      {/* ── Agent sidebar ── */}
      <div className="w-44 bg-slate-900 border-r border-slate-800 flex flex-col shrink-0">
        <div className="px-3 py-2 border-b border-slate-800">
          <span className="text-xs text-slate-500 uppercase tracking-widest">Agents</span>
        </div>
        <div className="flex-1 overflow-y-auto">
          {ALL_AGENTS.map(name => {
            const info = agentInfoMap[name]
            const isActive = agent === name
            return (
              <button
                key={name}
                onClick={() => switchAgent(name)}
                disabled={sending}
                className={`w-full text-left px-3 py-2.5 border-b border-slate-800/50 transition-colors ${
                  isActive
                    ? 'bg-slate-800 border-l-2 border-l-cyan-500'
                    : 'hover:bg-slate-800/50 border-l-2 border-l-transparent'
                }`}
              >
                <div className={`text-xs font-medium ${isActive ? 'text-cyan-400' : 'text-slate-300'}`}>
                  {name}
                </div>
                <div className="text-slate-600 text-xs mt-0.5">
                  {info?.role ?? '…'}
                </div>
                {info?.message_count && info.message_count > 0 ? (
                  <div className="text-slate-700 text-xs mt-0.5">{info.message_count} msgs</div>
                ) : null}
              </button>
            )
          })}
        </div>
      </div>

      {/* ── Main area ── */}
      <div className="flex flex-col flex-1 overflow-hidden">

        {/* ── Top bar ── */}
        <div className="flex items-center gap-3 px-4 py-2 border-b border-slate-700 bg-slate-900 shrink-0 flex-wrap">
          {/* Mode toggle */}
          <div className="flex items-center bg-slate-800 rounded p-0.5 gap-0.5">
            <button
              onClick={() => switchMode('chat')}
              className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                mode === 'chat' ? 'bg-cyan-700 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >Chat</button>
            <button
              onClick={() => switchMode('task')}
              className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                mode === 'task' ? 'bg-purple-700 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >Task</button>
          </div>

          {/* Agent identity */}
          <div className="flex items-center gap-2 text-xs">
            <span className="text-cyan-400 font-medium">{agent}</span>
            {currentAgent?.role && (
              <span className="text-slate-500">· {currentAgent.role}</span>
            )}
            {currentAgent?.identity_file && (
              <span className="text-slate-700 font-mono text-xs hidden xl:inline">
                {currentAgent.identity_file.replace('workspace/', '')}
              </span>
            )}
          </div>

          {/* Provider/model badge */}
          <div className="ml-auto flex items-center gap-2">
            {currentAgent?.model && (
              <span className="text-xs bg-slate-800 border border-slate-700 px-2 py-0.5 rounded text-slate-400">
                {currentAgent.provider}/{currentAgent.model}
              </span>
            )}
            {mode === 'chat' && (
              <span className="text-xs text-cyan-600 border border-cyan-900 bg-cyan-950/30 px-2 py-0.5 rounded">
                direct · no task
              </span>
            )}
            {mode === 'task' && activeTaskId && (
              <span className="text-xs text-amber-400 border border-amber-900 bg-amber-950/30 px-2 py-0.5 rounded animate-pulse">
                {activeTaskId}…
              </span>
            )}
            {mode === 'task' && !activeTaskId && (
              <span className="text-xs text-purple-400 border border-purple-900 bg-purple-950/30 px-2 py-0.5 rounded">
                task engine
              </span>
            )}
          </div>
        </div>

        {/* ── Messages ── */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.length === 0 && (
            <div className="text-center mt-16 space-y-3">
              <div className={`text-sm font-medium ${mode === 'chat' ? 'text-cyan-700' : 'text-purple-700'}`}>
                {agent} · {currentAgent?.role ?? ''}
              </div>
              <div className="text-slate-600 text-xs max-w-sm mx-auto">
                {mode === 'chat'
                  ? `Talking to ${agent} in chat mode. Replies are direct — no task created.`
                  : `Task mode. Describe work for the ${agent} to execute. Creates a tracked task.`}
              </div>
              {currentAgent?.identity_file && (
                <div className="text-slate-700 text-xs font-mono">
                  {currentAgent.identity_file.replace('workspace/', '')}
                </div>
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
                <div className="text-slate-700 text-xs mt-1">{m.ts.slice(11, 19)}</div>
              </div>
            </div>
          ))}
          <div ref={endRef} />
        </div>

        {/* ── Input ── */}
        <div className={`p-3 border-t shrink-0 ${
          mode === 'chat' ? 'border-cyan-900/50 bg-cyan-950/10' : 'border-purple-900/50 bg-purple-950/10'
        }`}>
          <div className="flex gap-2">
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={onKey}
              placeholder={
                mode === 'chat'
                  ? `Ask ${agent} anything…`
                  : `Describe a task for ${agent} to execute…`
              }
              rows={2}
              className="flex-1 bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded px-3 py-2 resize-none outline-none focus:border-cyan-700 placeholder-slate-600"
            />
            <button
              onClick={send}
              disabled={sending || !input.trim()}
              className={`px-4 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded text-xs font-medium transition-colors shrink-0 ${
                mode === 'chat' ? 'bg-cyan-700 hover:bg-cyan-600' : 'bg-purple-700 hover:bg-purple-600'
              }`}
            >
              {sending ? '…' : mode === 'chat' ? 'Send' : 'Create Task'}
            </button>
          </div>
          <div className="text-slate-700 text-xs mt-1">Enter to send · Shift+Enter for newline</div>
        </div>
      </div>
    </div>
  )
}
