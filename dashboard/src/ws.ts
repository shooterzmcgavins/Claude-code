import { WsEvent } from './types'

type Listener = (e: WsEvent) => void

class WSClient {
  private ws: WebSocket | null = null
  private listeners = new Set<Listener>()
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private reconnectDelay = 1000
  connected = false

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) return
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    const url = `${proto}://${location.host}/ws`
    this.ws = new WebSocket(url)

    this.ws.onopen = () => {
      this.connected = true
      this.reconnectDelay = 1000
      this.emit({ type: '_connected' })
    }

    this.ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data) as WsEvent
        if (data.type !== 'ping') this.emit(data)
      } catch {}
    }

    this.ws.onclose = () => {
      this.connected = false
      this.emit({ type: '_disconnected' })
      this.scheduleReconnect()
    }

    this.ws.onerror = () => {
      this.ws?.close()
    }
  }

  private emit(e: WsEvent) {
    this.listeners.forEach(fn => fn(e))
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) return
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null
      this.reconnectDelay = Math.min(this.reconnectDelay * 2, 15000)
      this.connect()
    }, this.reconnectDelay)
  }

  subscribe(fn: Listener): () => void {
    this.listeners.add(fn)
    return () => { this.listeners.delete(fn) }
  }
}

export const wsClient = new WSClient()
