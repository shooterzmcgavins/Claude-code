import { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Overview from './pages/Overview'
import Chat from './pages/Chat'
import Tasks from './pages/Tasks'
import Agents from './pages/Agents'
import Events from './pages/Events'
import Reports from './pages/Reports'
import Memory from './pages/Memory'
import Models from './pages/Models'
import Approvals from './pages/Approvals'
import { wsClient } from './ws'
import { WsEvent } from './types'

export default function App() {
  const [connected, setConnected] = useState(false)
  const [pendingApprovals, setPendingApprovals] = useState(0)

  useEffect(() => {
    wsClient.connect()
    const unsub = wsClient.subscribe((e: WsEvent) => {
      if (e.type === '_connected') setConnected(true)
      if (e.type === '_disconnected') setConnected(false)
      if (e.type === 'approval.pending') setPendingApprovals(n => n + 1)
      if (e.type === 'approval.resolved') setPendingApprovals(n => Math.max(0, n - 1))
    })
    return unsub
  }, [])

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout connected={connected} pendingApprovals={pendingApprovals} />}>
          <Route index element={<Navigate to="/overview" replace />} />
          <Route path="overview" element={<Overview />} />
          <Route path="chat" element={<Chat />} />
          <Route path="tasks" element={<Tasks />} />
          <Route path="agents" element={<Agents />} />
          <Route path="events" element={<Events />} />
          <Route path="reports" element={<Reports />} />
          <Route path="memory" element={<Memory />} />
          <Route path="models" element={<Models />} />
          <Route path="approvals" element={<Approvals setPendingApprovals={setPendingApprovals} />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
