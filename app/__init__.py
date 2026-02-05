"""
Main Flask application factory.
"""
from pathlib import Path

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

from app.config import Config
from app.database import SessionLocal, init_db
from app.models import ExchangeRate, User
from app.services import user_service
from sqlalchemy import func, select

# Auto-detect async mode:
# - Use 'eventlet' for production (Gunicorn with eventlet workers)
# - Use 'threading' for local development
# - Allow override via SOCKETIO_ASYNC_MODE env var
import os

# Check if we're running in production (Gunicorn or Render)
# Render sets PORT env var, Gunicorn sets GUNICORN_CMD_ARGS
is_production = (
    os.environ.get('GUNICORN_CMD_ARGS') is not None or 
    os.environ.get('SERVER_SOFTWARE', '').startswith('gunicorn') or
    os.environ.get('PORT') is not None  # Render sets this
)

# Default async mode based on environment
if os.environ.get('SOCKETIO_ASYNC_MODE'):
    # Explicit override
    async_mode = os.environ.get('SOCKETIO_ASYNC_MODE')
elif is_production:
    # Production: use eventlet (required for Gunicorn eventlet workers)
    async_mode = 'eventlet'
else:
    # Local development: use threading (works without eventlet)
    async_mode = 'threading'

socketio = SocketIO(cors_allowed_origins=Config.ALLOWED_ORIGINS, async_mode=async_mode)

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR.parent / "templates"


def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__, template_folder=str(TEMPLATE_DIR))
    app.config.from_object(config_class)
    
    CORS(app, origins=config_class.ALLOWED_ORIGINS, supports_credentials=True)
    
    # Initialize SocketIO
    socketio.init_app(app)
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.api import api_bp
    from app.routes.internal import internal_bp
    from app.routes.websocket_routes import ws_bp
    from app.routes.sse_routes import sse_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(internal_bp)
    app.register_blueprint(ws_bp)
    app.register_blueprint(sse_bp)

    # Initialize persistence + service layer
    # Do this synchronously but quickly - database init is fast, user service uses background thread
    import logging
    
    try:
        with app.app_context():
            init_db()
            user_service.start()
    except Exception as e:
        logging.error(f"Error during database/service initialization: {e}", exc_info=True)
    
    _start_sse_cleanup_thread()
    _start_active_disconnect_worker(app)
    
    return app


def _start_active_disconnect_worker(app):
    """
    Start background worker that disconnects users removed from database.
    Runs every 10 seconds, checks all connected users, disconnects if not in DB.
    """
    import threading
    import time
    import logging
    
    logger = logging.getLogger(__name__)
    
    def active_disconnect_loop():
        """Background loop to disconnect users removed from database."""
        from app.websocket_manager import websocket_manager
        from app import socketio
        
        while True:
            try:
                time.sleep(10)  # Run every 10 seconds
                
                # Get all currently connected usernames (thread-safe snapshot)
                connected_users = set()
                sids_to_disconnect = []
                
                # Create snapshot of clients (dict access is thread-safe for reading in Python)
                clients_snapshot = dict(websocket_manager.clients)
                for sid, client_info in clients_snapshot.items():
                    username = client_info.get('username')
                    if username:
                        connected_users.add(username.lower())
                
                if not connected_users:
                    continue
                
                # Batch query: check which users still exist in DB
                try:
                    with app.app_context():
                        from app.database import SessionLocal
                        with SessionLocal() as session:
                            valid_users = session.execute(
                                select(func.lower(User.username)).where(
                                    func.lower(User.username).in_(connected_users)
                                )
                            ).scalars().all()
                            
                            valid_users_set = {u.lower() for u in valid_users}
                            
                            # Find users to disconnect (in connected but not in DB)
                            users_to_disconnect = connected_users - valid_users_set
                            
                            if users_to_disconnect:
                                logger.info(f"Active disconnect: Found {len(users_to_disconnect)} users to disconnect")
                                
                                # Collect SIDs to disconnect (use snapshot)
                                for sid, client_info in clients_snapshot.items():
                                    username = client_info.get('username')
                                    if username and username.lower() in users_to_disconnect:
                                        sids_to_disconnect.append((sid, client_info.get('namespace', '/'), username))
                                
                                # Disconnect each user
                                for sid, namespace, username in sids_to_disconnect:
                                    try:
                                        socketio.server.disconnect(sid, namespace=namespace)
                                        websocket_manager.remove_client(sid)
                                        logger.info(f"Disconnected user: {username} (removed from DB)")
                                    except Exception as e:
                                        logger.warning(f"Error disconnecting {username}: {e}")
                
                except Exception as e:
                    logger.error(f"Error in active disconnect worker: {e}", exc_info=True)
            
            except Exception as e:
                logger.error(f"Error in active disconnect loop: {e}", exc_info=True)
                time.sleep(10)  # Wait before retrying
    
    worker_thread = threading.Thread(target=active_disconnect_loop, daemon=True, name="Active-Disconnect-Worker")
    worker_thread.start()
    logger.info("Active disconnect worker started")


def _start_sse_cleanup_thread():
    """Start background thread to clean up stale SSE connections."""
    import threading
    import time
    import logging
    
    def cleanup_loop():
        """Background loop to clean up stale SSE connections."""
        from app.sse_manager import sse_manager
        
        while True:
            try:
                time.sleep(60)  # Run every minute
                sse_manager.cleanup_stale_connections(timeout_seconds=120)
            except Exception as e:
                logging.error(f"Error in SSE cleanup loop: {e}")
    
    cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True, name="SSE-Cleanup")
    cleanup_thread.start()


