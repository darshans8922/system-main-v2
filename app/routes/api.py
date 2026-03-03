from flask import Blueprint, jsonify, request
from sqlalchemy import select, func

from app.config import Config
from app.database import db_session
from app.models import User, ExchangeRate
from app.rate_limit import get_username_key, limiter

api_bp = Blueprint('api', __name__, url_prefix='/api')

def _get_connected_usernames():
    """Return set of usernames currently connected via WebSocket or SSE (lowercase)."""
    connected = set()
    try:
        from app.websocket_manager import websocket_manager
        clients_snapshot = dict(websocket_manager.clients)
        for sid, info in clients_snapshot.items():
            u = info.get('username')
            if u:
                connected.add(u.lower())
    except Exception:
        pass
    try:
        from app.sse_manager import sse_manager
        with sse_manager.lock:
            for username in sse_manager.connections.keys():
                if username:
                    connected.add(username.lower())
    except Exception:
        pass
    return connected


@api_bp.route('/ingest', methods=['POST', 'GET'])
def ingest():
    return jsonify({
        'error': 'HTTP ingest has been disabled',
        'next_steps': 'Connect to the /ws/ingest Socket.IO namespace and include the shared ingest token.'
    }), 410


@api_bp.route('/status')
def api_status():
    from app.utils.decoy import generate_decoy_response
    return generate_decoy_response()


@api_bp.route('/info')
def api_info():
    from app.utils.decoy import generate_decoy_response
    return generate_decoy_response()


@api_bp.route('/exchange-rates', methods=['GET'])
def get_exchange_rates():
    try:
        with db_session() as session:
            result = session.execute(
                select(
                    func.upper(func.trim(ExchangeRate.target_currency)).label('currency'),
                    ExchangeRate.rate_from_usd
                )
            ).mappings().all()
            
            rates = [dict(row) for row in result]
            
            return jsonify({
                'rates': rates,
                'count': len(rates)
            }), 200
            
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


# Rate limits: per-IP (max usernames one IP can send in 1 min) and per-username (Flask-Limiter; Cloudflare cannot key by username)
_IP_LIMIT = f"{Config.RATELIMIT_IP_USERNAME_PER_MINUTE} per minute"
_USERNAME_LIMIT = f"{Config.RATELIMIT_PER_USERNAME_PER_MINUTE} per minute"


@api_bp.route('/users/claims/convert-to-usd', methods=['POST'])
@limiter.limit(_IP_LIMIT)
@limiter.limit(
    _USERNAME_LIMIT,
    key_func=get_username_key,
    exempt_when=lambda: get_username_key() is None,
)
def convert_to_usd():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body must be JSON'}), 400
        
        username = data.get('username')
        target_currency = data.get('target_currency')
        amount = data.get('amount')
        
        if not username or not target_currency or amount is None:
            return jsonify({'error': 'username, target_currency, and amount are required'}), 400
        
        try:
            amount = float(amount)
            if amount < 0:
                return jsonify({'error': 'amount must be non-negative'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'amount must be a valid number'}), 400
        
        if not isinstance(target_currency, str):
            return jsonify({'error': 'target_currency must be a string'}), 400
        
        currency = target_currency.strip().upper()
        if not currency or len(currency) < 3 or len(currency) > 10:
            return jsonify({'error': 'target_currency must be 3-10 characters (e.g., BTC, USDT, INR)'}), 400
        
        with db_session() as session:
            user = session.execute(
                select(User).where(func.lower(User.username) == username.lower())
            ).scalar_one_or_none()
            
            if not user:
                return jsonify({'error': f'User with username "{username}" not found'}), 404

            # Only registered users (in backend DB) can convert to USD — no connection check

            # Fetch exchange rate directly from database
            rate_row = session.execute(
                select(ExchangeRate).where(
                    func.upper(func.trim(ExchangeRate.target_currency)) == currency
                )
            ).scalar_one_or_none()
            
            if not rate_row or not rate_row.rate_from_usd:
                return jsonify({
                    'error': f'Exchange rate for currency "{currency}" not found'
                }), 404
            
            rate_from_usd = float(rate_row.rate_from_usd)
            
            if rate_from_usd <= 0:
                return jsonify({
                    'error': f'Invalid exchange rate for currency "{currency}"'
                }), 400
            
            converted_usd = amount / rate_from_usd
            
            if user.usd_claim_amount is None:
                user.usd_claim_amount = 0.0
            user.usd_claim_amount += converted_usd
            
            final_amount = user.usd_claim_amount
        
        return jsonify({
            'success': True,
            'usd_claim_amount': final_amount,
        }), 200
            
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500
