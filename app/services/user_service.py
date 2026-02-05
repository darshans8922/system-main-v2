"""
In-memory cache for all users with DB fallback.
Database is the source of truth.
"""
from __future__ import annotations

import threading
import time
from typing import Dict, Optional

from sqlalchemy import func, select

from app.config import Config
from app.database import SessionLocal
from app.models import User


class UserService:
    """
    In-memory cache for all users with TTL.
    Pinned users never expire, others expire after TTL.
    """

    def __init__(self):
        self._cache: Dict[str, dict] = {}
        self._lock = threading.Lock()
        self._pinned_users = {u.lower() for u in Config.PINNED_USERS}
        self._ttl = 300  # 5 minutes TTL for non-pinned users
        self._max_size = 5000  # Max cache size

    def start(self) -> None:
        """Preload pinned users into local cache on startup."""
        try:
            self._preload_pinned_users()
        except Exception as e:
            import logging
            logging.warning(f"UserService: Failed to preload pinned users: {e}")

    def stop(self) -> None:
        """Cleanup."""
        pass

    def get_user(self, username: str) -> Optional[dict]:
        """
        Get user from cache or DB.
        Returns user dict with user_id and username, or None if not found.
        """
        normalized = self._normalize(username)
        if not normalized:
            return None

        # Check cache first
        cached = self._get_from_cache(normalized)
        if cached:
            return cached

        # DB lookup
        return self._lookup_and_cache(normalized)

    def _get_from_cache(self, normalized: str) -> Optional[dict]:
        """Get user from cache if not expired."""
        with self._lock:
            entry = self._cache.get(normalized)
            if not entry:
                return None
            
            # Pinned users never expire
            if normalized in self._pinned_users:
                return entry
            
            # Check expiration
            if entry.get("expires_at", 0) < time.time():
                del self._cache[normalized]
                return None
            
            return entry

    def _lookup_and_cache(self, normalized: str) -> Optional[dict]:
        """Lookup user in DB and cache it."""
        try:
            with SessionLocal() as session:
                row = session.execute(
                    select(User).where(func.lower(User.username) == normalized)
                ).scalar_one_or_none()

                if not row:
                    return None

                expires_at = float('inf') if normalized in self._pinned_users else time.time() + self._ttl
                entry = {
                    "user_id": row.id,
                    "username": row.username,
                    "expires_at": expires_at,
                }

                # Cache with size limit
                with self._lock:
                    if len(self._cache) >= self._max_size:
                        # Evict expired entries
                        now = time.time()
                        expired = [
                            k for k, v in self._cache.items()
                            if k not in self._pinned_users and v.get("expires_at", 0) < now
                        ]
                        for k in expired[:100]:  # Remove up to 100 expired entries
                            self._cache.pop(k, None)
                    
                    self._cache[normalized] = entry

                return entry
        except Exception:
            return None

    def _preload_pinned_users(self) -> None:
        """Preload pinned users into local cache on startup."""
        try:
            with SessionLocal() as session:
                for username in self._pinned_users:
                    try:
                        row = session.execute(
                            select(User).where(func.lower(User.username) == username)
                        ).scalar_one_or_none()
                        
                        if row:
                            with self._lock:
                                self._cache[username] = {
                                    "user_id": row.id,
                                    "username": row.username,
                                    "expires_at": float('inf'),
                                }
                    except Exception:
                        pass
        except Exception:
            pass

    def _normalize(self, username: Optional[str]) -> Optional[str]:
        if username is None:
            return None
        username = str(username).strip()
        if not username or len(username) > 64:
            return None
        return username.lower()


user_service = UserService()

