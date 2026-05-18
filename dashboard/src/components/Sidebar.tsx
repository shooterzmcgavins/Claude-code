import { NavLink } from 'react-router-dom'

const NAV = [
  { to: '/overview', icon: '⬡', label: 'Overview' },
  { to: '/health',   icon: '◎', label: 'Health' },
  { to: '/chat',     icon: '◈', label: 'Chat' },
  { to: '/tasks',    icon: '◻', label: 'Tasks' },
  { to: '/agents',   icon: '◇', label: 'Agents' },
  { to: '/events',   icon: '≋', label: 'Events' },
  { to: '/reports',  icon: '◈', label: 'Reports' },
  { to: '/files',    icon: '📁', label: 'Files' },
  { to: '/memory',   icon: '○', label: 'Memory' },
  { to: '/models',   icon: '◆', label: 'Models' },
  { to: '/approvals',icon: '⚠', label: 'Approvals' },
  { to: '/settings', icon: '⚙', label: 'Settings' },
]

interface Props { pendingApprovals: number }

export default function Sidebar({ pendingApprovals }: Props) {
  return (
    <nav className="w-44 bg-slate-900 border-r border-slate-800 flex flex-col shrink-0">
      {/* Logo */}
      <div className="px-4 py-4 border-b border-slate-800">
        <div className="text-cyan-400 text-glow-cyan font-bold tracking-wider text-sm">MISSION</div>
        <div className="text-cyan-400 text-glow-cyan font-bold tracking-wider text-sm">CONTROL</div>
      </div>

      {/* Nav items */}
      <div className="flex-1 py-2 overflow-y-auto">
        {NAV.map(({ to, icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-2 px-4 py-2 text-xs transition-colors relative
               ${isActive
                 ? 'text-cyan-400 bg-slate-800 border-r-2 border-cyan-400'
                 : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'}`
            }
          >
            <span className="w-4 text-center">{icon}</span>
            <span>{label}</span>
            {label === 'Approvals' && pendingApprovals > 0 && (
              <span className="ml-auto bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">
                {pendingApprovals}
              </span>
            )}
          </NavLink>
        ))}
      </div>

      <div className="px-4 py-3 border-t border-slate-800 text-slate-600 text-xs">
        v1.0
      </div>
    </nav>
  )
}
