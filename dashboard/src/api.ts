const BASE = '/api'

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`)
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
  return r.json()
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
  return r.json()
}

async function put<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
  return r.json()
}

export const api = {
  overview: () => get<any>('/chat/overview'),
  tasks: {
    list: (status?: string) => get<any[]>(`/tasks${status ? `?status=${status}` : ''}`),
    get: (id: string) => get<any>(`/tasks/${id}`),
    create: (title: string, description?: string, agent?: string) =>
      post<any>('/tasks', { title, description: description ?? title, agent }),
  },
  agents: {
    list: () => get<any[]>('/agents'),
    get: (name: string) => get<any>(`/agents/${name}`),
  },
  events: {
    list: (n = 50, agent?: string, type?: string) => {
      const params = new URLSearchParams({ n: String(n) })
      if (agent) params.set('agent', agent)
      if (type) params.set('type', type)
      return get<any[]>(`/events?${params}`)
    },
  },
  reports: {
    list: () => get<any[]>('/reports'),
    get: (taskId: string) => get<any>(`/reports/${taskId}`),
  },
  memory: {
    list: () => get<any[]>('/memory'),
    get: (key: string) => get<any>(`/memory/${key}`),
    write: (key: string, content: string) => put<any>(`/memory/${key}`, { content }),
  },
  models: {
    get: () => get<any>('/models'),
  },
  approvals: {
    pending: () => get<any[]>('/approvals/pending'),
    resolve: (id: string, approved: boolean) =>
      post<any>(`/approvals/${id}/resolve`, { approved }),
  },
  chat: {
    send: (message: string, agent?: string, session_id?: string) =>
      post<any>('/chat', { message, agent, session_id }),
    sessions: () => get<any[]>('/chat/sessions'),
    session: (id: string) => get<any>(`/chat/sessions/${id}`),
  },
}
