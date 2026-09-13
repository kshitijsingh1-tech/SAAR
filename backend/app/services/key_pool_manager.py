import os
import time
import logging
from typing import List, Dict, Any, Optional, Tuple

try:
    from dotenv import load_dotenv
    _env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), ".env")
    if os.path.exists(_env_file):
        load_dotenv(_env_file, override=True)
    else:
        # Also check d:\bytebuild\backend\.env
        _backend_env = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
        if os.path.exists(_backend_env):
            load_dotenv(_backend_env, override=True)
        else:
            load_dotenv(override=True)
except ImportError:
    pass

logger = logging.getLogger("saar.key_pool")

class KeyState:
    def __init__(self, key: str, provider: str):
        self.key = key.strip()
        self.provider = provider
        self.cooldown_until: float = 0.0
        self.requests_served: int = 0
        self.errors_count: int = 0
        self.is_invalid: bool = False
        self.last_used: float = 0.0

    @property
    def is_available(self) -> bool:
        if self.is_invalid:
            return False
        return time.time() >= self.cooldown_until

    @property
    def masked_key(self) -> str:
        if len(self.key) <= 8:
            return "***"
        return f"{self.key[:6]}...{self.key[-4:]}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.masked_key,
            "provider": self.provider,
            "is_available": self.is_available,
            "is_invalid": self.is_invalid,
            "cooldown_remaining_sec": max(0, int(self.cooldown_until - time.time())),
            "requests_served": self.requests_served,
            "errors_count": self.errors_count,
        }


class KeyPoolManager:
    """
    Intelligent Load-Balancing & Failover Pool for Multimodal & LLM API Keys.
    Supports Google Gemini, Groq, OpenRouter, and OpenAI.
    Enables horizontal scaling to 800+ requests/day across free-tier keys.
    """
    _instance: Optional["KeyPoolManager"] = None

    def __init__(self):
        self.pools: Dict[str, List[KeyState]] = {
            "gemini": [],
            "groq": [],
            "openrouter": [],
            "openai": []
        }
        self.reload_keys_from_env()

    @classmethod
    def get_instance(cls) -> "KeyPoolManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def reload_keys_from_env(self) -> None:
        """Parse comma-separated or single keys from environment variables."""
        # 1. Gemini Keys (GEMINI_API_KEYS or GEMINI_API_KEY)
        gemini_raw = os.getenv("GEMINI_API_KEYS") or os.getenv("GEMINI_API_KEY") or ""
        self._load_provider_keys("gemini", gemini_raw)

        # 2. Groq Keys (GROQ_API_KEYS or GROQ_API_KEY)
        groq_raw = os.getenv("GROQ_API_KEYS") or os.getenv("GROQ_API_KEY") or ""
        self._load_provider_keys("groq", groq_raw)

        # 3. OpenRouter Keys (OPENROUTER_API_KEYS or OPENROUTER_API_KEY)
        openrouter_raw = os.getenv("OPENROUTER_API_KEYS") or os.getenv("OPENROUTER_API_KEY") or ""
        self._load_provider_keys("openrouter", openrouter_raw)

        # 4. OpenAI Keys (OPENAI_API_KEYS or OPENAI_API_KEY)
        openai_raw = os.getenv("OPENAI_API_KEYS") or os.getenv("OPENAI_API_KEY") or ""
        self._load_provider_keys("openai", openai_raw)

    def _load_provider_keys(self, provider: str, raw_val: str) -> None:
        if not raw_val:
            return
        # Split by comma or semicolon or newline
        keys = [k.strip() for k in raw_val.replace(";", ",").replace("\n", ",").split(",") if k.strip()]
        existing_keys = {ks.key: ks for ks in self.pools[provider]}

        new_pool: List[KeyState] = []
        for k in keys:
            if k in existing_keys:
                new_pool.append(existing_keys[k])
            else:
                new_pool.append(KeyState(key=k, provider=provider))
        self.pools[provider] = new_pool
        logger.info(f"[KeyPoolManager] Loaded {len(new_pool)} keys for provider '{provider}'")

    def get_available_keys(self, provider: str) -> List[KeyState]:
        """Return all healthy keys for the provider, prioritized by least-used / round-robin."""
        pool = self.pools.get(provider, [])
        available = [ks for ks in pool if ks.is_available]
        # Sort by least requests served and least recently used
        available.sort(key=lambda ks: (ks.requests_served, ks.last_used))
        return available

    def record_success(self, provider: str, key: str) -> None:
        """Mark successful execution on this key."""
        for ks in self.pools.get(provider, []):
            if ks.key == key:
                ks.requests_served += 1
                ks.errors_count = 0
                ks.last_used = time.time()
                break

    def record_quota_exhausted(self, provider: str, key: str, cooldown_sec: float = 60.0) -> None:
        """
        Mark a 429 quota exhaustion on this key.
        Sets a cooldown period so subsequent requests instantly route to other keys.
        """
        for ks in self.pools.get(provider, []):
            if ks.key == key:
                ks.cooldown_until = time.time() + cooldown_sec
                ks.errors_count += 1
                ks.last_used = time.time()
                logger.warning(
                    f"[KeyPoolManager] Key {ks.masked_key} on {provider} rate-limited (429). "
                    f"Cooldown for {cooldown_sec:.1f}s. Available fallback keys: {len([k for k in self.pools[provider] if k.is_available])}"
                )
                break

    def record_key_invalid(self, provider: str, key: str, reason: str = "Invalid API Key") -> None:
        """Permanently disable an invalid key in the pool so it doesn't slow down the system."""
        for ks in self.pools.get(provider, []):
            if ks.key == key:
                ks.is_invalid = True
                logger.error(f"[KeyPoolManager] Key {ks.masked_key} on {provider} marked permanently invalid ({reason}).")
                break

    def get_status(self) -> Dict[str, Any]:
        """Return comprehensive telemetry of the key pool."""
        telemetry = {}
        for prov, keys in self.pools.items():
            total = len(keys)
            active = len([k for k in keys if k.is_available])
            in_cooldown = len([k for k in keys if not k.is_invalid and not k.is_available])
            invalid = len([k for k in keys if k.is_invalid])
            served = sum(k.requests_served for k in keys)
            telemetry[prov] = {
                "total_keys": total,
                "active_keys": active,
                "cooldown_keys": in_cooldown,
                "invalid_keys": invalid,
                "total_requests_served": served,
                "keys_detail": [k.to_dict() for k in keys]
            }
        return telemetry

# Global singleton helper
key_pool = KeyPoolManager.get_instance()
