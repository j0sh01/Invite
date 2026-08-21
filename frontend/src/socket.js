import { io } from 'socket.io-client'
import { socketio_port } from '../../../../sites/common_site_config.json'

export function initSocket() {
  let host = window.location.hostname
  let siteName = window.site_name
  let port = window.location.port ? `:${socketio_port}` : ''
  let protocol = port ? 'http' : 'https'
  let url = `${protocol}://${host}${port}/${siteName}`

  let socket = io(url, {
    withCredentials: true,
    reconnectionAttempts: 5,
  })

  // frappe-ui's vite plugin handles the refetch_resource event internally
  // and reloads cached resources automatically. We just need to emit the
  // socket connection so frappe-ui can hook into it.
  return socket
}
