"""
Main API routes (no HTML rendering).
"""
from pathlib import Path
from urllib.parse import urlparse

from flask import Blueprint, Response, jsonify, request, send_from_directory

from app.config import Config
from app.utils.decoy import generate_decoy_response

main_bp = Blueprint('main', __name__)


def _relay_domain_allowed(url: str) -> bool:
    """Return True if the URL's host is in RELAY_ALLOWED_DOMAINS."""
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
        host = parsed.netloc.split(":")[0].lower()
        return host in Config.RELAY_ALLOWED_DOMAINS
    except Exception:
        return False


@main_bp.route('/health')
def health():
    """Health check endpoint for UptimeRobot monitoring."""
    return jsonify({
        'status': 'healthy',
        'service': 'code-server'
    }), 200


@main_bp.route('/relay')
def relay():
    """Fetch a URL and return its content (CSP bypass). Only allowed domains may be fetched."""
    target_url = request.args.get('url')
    if not target_url:
        return jsonify({'error': 'Missing url parameter'}), 400

    if not _relay_domain_allowed(target_url):
        return jsonify({'error': 'Domain not allowed for relay'}), 403

    try:
        import requests
        response = requests.get(target_url, timeout=10)
        return Response(
            response.content,
            status=response.status_code,
            headers={'Content-Type': response.headers.get('Content-Type', 'text/html')}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Decoy routes (intentionally added, no real purpose)
@main_bp.route('/')
def index():
    """Decoy route."""
    return generate_decoy_response()


@main_bp.route('/dashboard')
def dashboard():
    """Decoy route."""
    return generate_decoy_response()


@main_bp.route('/admin')
def admin():
    """Decoy route."""
    return generate_decoy_response()


@main_bp.route('/api')
def api_index():
    """Decoy route."""
    return generate_decoy_response()


@main_bp.route('/status')
def status():
    """Decoy route."""
    return generate_decoy_response()


@main_bp.route('/test')
def test_page():
    """Serve the Socket.IO test HTML page."""
    tests_dir = Path(__file__).parent.parent.parent / 'tests'
    return send_from_directory(str(tests_dir), 'socket_test.html')


@main_bp.route('/sse-test')
def sse_test_page():
    """Serve the SSE /embed-stream test HTML page."""
    tests_dir = Path(__file__).parent.parent.parent / 'tests'
    return send_from_directory(str(tests_dir), 'sse_test.html')


@main_bp.route('/load-test')
def load_test_page():
    """Serve the SSE load test HTML page."""
    tests_dir = Path(__file__).parent.parent.parent / 'tests'
    return send_from_directory(str(tests_dir), 'load_test_sse.html')



