"""
SSE (Server-Sent Events) connection and message broadcasting manager.
"""
import queue
import threading
import time
from collections import defaultdict
from typing import Dict, List, Optional


class SSEManager:
    """Manages SSE connections and code broadcasting."""
    
    def __init__(self, max_connections: int = 500):
        # username -> list of connection IDs
        self.connections: Dict[str, List[str]] = defaultdict(list)
        # username -> message queue
        self.message_queues: Dict[str, queue.Queue] = {}
        # connection_id -> health tracking
        self.connection_health: Dict[str, dict] = {}
        self.lock = threading.Lock()
        self.max_queue_size = 100
        self.max_connections = max_connections
    
    def add_connection(self, username: str, connection_id: str) -> None:
        """Add a new SSE connection for a user."""
        with self.lock:
            # Check connection limit
            current_count = sum(len(conns) for conns in self.connections.values())
            if current_count >= self.max_connections:
                raise RuntimeError(f"Maximum SSE connections ({self.max_connections}) reached")
            # Auto-disconnect previous connections for same user (allow only 1 active connection)
            if username in self.connections and self.connections[username]:
                old_connections = self.connections[username].copy()
                for old_conn_id in old_connections:
                    if old_conn_id in self.connection_health:
                        del self.connection_health[old_conn_id]
                    # Try to send disconnect message
                    if username in self.message_queues:
                        try:
                            disconnect_msg = {
                                'type': 'force_disconnect',
                                'message': 'New connection detected - this session will be closed',
                                'timestamp': int(time.time())
                            }
                            self.message_queues[username].put_nowait(disconnect_msg)
                        except queue.Full:
                            pass
                self.connections[username].clear()
            
            # Initialize message queue if doesn't exist
            if username not in self.message_queues:
                self.message_queues[username] = queue.Queue(maxsize=self.max_queue_size)
            
            # Add new connection
            self.connections[username].append(connection_id)
            
            # Initialize health tracking
            self.connection_health[connection_id] = {
                'username': username,
                'last_ping': 0,
                'last_pong': time.time(),
                'ping_count': 0
            }
    
    def remove_connection(self, username: str, connection_id: str) -> None:
        """Remove an SSE connection."""
        with self.lock:
            if username in self.connections:
                if connection_id in self.connections[username]:
                    self.connections[username].remove(connection_id)
                
                # Clean up if no more connections
                if not self.connections[username]:
                    del self.connections[username]
                    if username in self.message_queues:
                        del self.message_queues[username]
            
            # Clean up health tracking
            if connection_id in self.connection_health:
                del self.connection_health[connection_id]
    
    def broadcast_code(self, code_data: dict) -> None:
        """
        Broadcast code to all SSE connections for the user.
        
        Args:
            code_data: Dictionary containing code information with username
        """
        username = code_data.get('username')
        if not username:
            return
        
        with self.lock:
            if username in self.message_queues:
                # Add value field as requested (value: 3)
                message = code_data.copy()
                if 'value' not in message:
                    message['value'] = 3
                
                # Try to add message to queue
                try:
                    self.message_queues[username].put_nowait(message)
                except queue.Full:
                    # Queue full, log and skip this message
                    import logging
                    logging.warning(
                        f"SSE message queue full for user '{username}', "
                        f"dropping message: {code_data.get('code', 'N/A')}"
                    )
    
    def get_message_queue(self, username: str) -> Optional[queue.Queue]:
        """Get message queue for a user."""
        with self.lock:
            return self.message_queues.get(username)
    
    def update_pong(self, connection_id: str) -> None:
        """Update last pong time for a connection."""
        with self.lock:
            if connection_id in self.connection_health:
                self.connection_health[connection_id]['last_pong'] = time.time()
    
    def get_connection_count(self) -> int:
        """Get total number of active SSE connections."""
        with self.lock:
            return sum(len(conns) for conns in self.connections.values())
    
    def cleanup_stale_connections(self, timeout_seconds: int = 120) -> int:
        """
        Remove connections that haven't responded to pings.
        
        Args:
            timeout_seconds: Time in seconds since last pong before considering connection stale
            
        Returns:
            Number of connections cleaned up
        """
        current_time = time.time()
        stale_connections = []
        
        with self.lock:
            for connection_id, health in list(self.connection_health.items()):
                time_since_pong = current_time - health.get('last_pong', 0)
                if time_since_pong > timeout_seconds:
                    stale_connections.append((health.get('username'), connection_id))
        
        # Remove stale connections
        for username, conn_id in stale_connections:
            self.remove_connection(username, conn_id)
        
        return len(stale_connections)
    
    def get_stats(self) -> dict:
        """Get statistics about SSE connections."""
        with self.lock:
            total_queued = sum(
                q.qsize() for q in self.message_queues.values()
            )
            return {
                'active_connections': self.get_connection_count(),
                'users_with_connections': len(self.connections),
                'total_queued_messages': total_queued,
                'total_health_tracked': len(self.connection_health)
            }


# Global instance
sse_manager = SSEManager()

