import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'

interface Props {
  connected: boolean
  pendingApprovals: number
}

export default function Layout({ connected, pendingApprovals }: Props) {
  return (
    <div className="flex h-screen bg-slate-950 overflow-hidden">
      <Sidebar pendingApprovals={pendingApprovals} />
      <div className="flex flex-col flex-1 overflow-hidden">
        {/* Top bar */}
        <header className="flex items-center justify-between px-4 py-2 border-b border-slate-800 bg-slate-900 shrink-0">
          <span className="text-xs text-slate-500 tracking-widest uppercase">AI Engineering Workspace</span>
          <div className="flex items-center gap-2 text-xs">
            <span className={`inline-block w-2 h-2 rounded-full ${connected ? 'bg-emerald-400' : 'bg-red-500'}`} />
            <span className={connected ? 'text-emerald-400' : 'text-red-400'}>
              {connected ? 'connected' : 'disconnected'}
            </span>
          </div>
        </header>
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
