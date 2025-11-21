"""
WSGI entry point for production.
"""
from app import create_app, socketio

app = create_app()


@app.before_request
def before_request():
    """Execute before each request."""
    pass


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)

