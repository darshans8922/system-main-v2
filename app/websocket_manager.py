"""
WebSocket connection and code broadcasting manager.
"""
from datetime import datetime
from typing import Optional


class WebSocketManager:
    """Manages WebSocket connections and code broadcasting."""
    
    def __init__(self):
        self.clients = {}  # {sid: {'namespace': str, 'username': str, 'connected_at': datetime}}
        self.code_history = []  # Store recent codes
        self.max_history = 100
    
    def add_client(self, sid, namespace='default', user=None):
        """Add a client to the manager."""
        self.clients[sid] = {
            'namespace': namespace,
            'username': user.get('username') if isinstance(user, dict) else None,
            'user_id': user.get('user_id') if isinstance(user, dict) else None,
            'connected_at': datetime.now()
        }
    
    def remove_client(self, sid):
        """Remove a client from the manager."""
        if sid in self.clients:
            del self.clients[sid]

    def get_client(self, sid) -> Optional[dict]:
        """Return client metadata if connected."""
        return self.clients.get(sid)
    
    def broadcast_code(self, code_data, socketio_instance=None):
        """
        Broadcast code to all connected clients (both Socket.IO and SSE).
        
        Args:
            code_data: Dictionary containing code information
            socketio_instance: SocketIO instance to use for broadcasting
        """
        # Add timestamp if not present
        if 'timestamp' not in code_data:
            code_data['timestamp'] = datetime.now().isoformat()
        
        # Store in history
        self.code_history.append(code_data)
        if len(self.code_history) > self.max_history:
            self.code_history.pop(0)
        
        # Broadcast to Socket.IO clients
        if socketio_instance:
            # Broadcast to /events namespace (code listeners)
            socketio_instance.emit('new_code', code_data, room='code_listeners', namespace='/events')
            
            # Also broadcast to default namespace
            socketio_instance.emit('new_code', code_data)
        
        # Broadcast to SSE clients
        from app.sse_manager import sse_manager
        sse_manager.broadcast_code(code_data)
    
    def get_client_count(self):
        """Get the number of connected clients."""
        return len(self.clients)
    
    def get_code_history(self, limit=10):
        """Get recent code history."""
        return self.code_history[-limit:]


# Global instance
websocket_manager = WebSocketManager()



