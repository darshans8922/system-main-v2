"""
Central rate limiting with Flask-Limiter.

- Per-IP limits use the real client IP (Cloudflare-aware via CF-Connecting-IP / X-Forwarded-For).
- Per-username limits key by username from request body (Cloudflare cannot do this).
"""
from flask import request
from flask_limiter import Limiter

from app.utils.cloudflare import get_real_client_ip


def get_username_key() -> str | None:
    """
    Key for rate limits that should be applied per username.
    Used on endpoints that accept username in JSON body (e.g. POST /api/users/claims/convert-to-usd).
    Returns None when username is missing so this limit is not applied for that request.
    """
    if not request.is_json:
        return None
    try:
        data = request.get_json(silent=True)
        username = (data or {}).get('username')
        if not username or not isinstance(username, str):
            return None
        return f"username:{username.strip().lower()}"
    except Exception:
        return None


def get_embed_stream_user_key() -> str | None:
    """
    Key for rate limits on /embed-stream: per user (from query param `user`).
    Returns None when user param is missing so the limit can be exempted.
    """
    user = request.args.get('user')
    if not user or not isinstance(user, str):
        return None
    return f"embed_stream:{user.strip().lower()}"


# Limiter is created without app; init_app() is called in create_app().
# Default key_func = get_real_client_ip so IP-based limits work behind Cloudflare.
limiter = Limiter(
    key_func=get_real_client_ip,
    default_limits=[],  # No global default; apply limits per-route
)
