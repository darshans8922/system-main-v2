"""
API routes (HTTP). Code ingestion now requires the WebSocket channel.
"""
from flask import Blueprint, jsonify

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/ingest', methods=['POST', 'GET'])
def ingest():
    """
    Legacy HTTP ingestion endpoint.
    HTTP ingestion has been disabled; clients must use the /ws/ingest WebSocket.
    """
    return jsonify({
        'error': 'HTTP ingest has been disabled',
        'next_steps': 'Connect to the /ws/ingest Socket.IO namespace and include the shared ingest token.'
    }), 410


# Decoy API routes
@api_bp.route('/status')
def api_status():
    """Decoy route."""
    from app.utils.decoy import generate_decoy_response
    return generate_decoy_response()


@api_bp.route('/info')
def api_info():
    """Decoy route."""
    from app.utils.decoy import generate_decoy_response
    return generate_decoy_response()

