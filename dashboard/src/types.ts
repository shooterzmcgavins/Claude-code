export type TaskStatus = 'pending' | 'in_progress' | 'needs_approval' | 'complete' | 'failed'

export interface Task {
  id: string
  title: string
  description: string
  status: TaskStatus
  agent: string | null
  created_at: string
  updated_at: string
  result: string | null
  tags: string[]
  has_report: boolean
}

export interface Agent {
  name: string
  role: string
  model: string
  tools: string | string[]
  keywords: string[]
  source_file: string
  system_prompt: string
  status: 'idle' | 'active'
  current_task: string | null
  last_activity: string | null
}

export interface WsEvent {
  type: string
  ts?: string
  task_id?: string
  agent?: string
  text?: string
  tool?: string
  args?: string
  approval_id?: string
  command?: string
  approved?: boolean
  [key: string]: unknown
}

export interface ChatMessage {
  ts: string
  session_id: string
  role: 'user' | 'assistant'
  content: string
  agent: string | null
  task_id: string | null
}

export interface ApprovalRequest {
  id: string
  agent: string
  command: string
  task_id: string | null
  created_at: string
}

export interface Overview {
  task_counts: Record<TaskStatus, number>
  total_tasks: number
  event_count: number
  uptime_seconds: number
  provider: string
  model: string
}
