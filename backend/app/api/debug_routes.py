"""TEMPORARY diagnostic endpoint — Resend configuration audit.

Read-only. Does not call any provider, does not send anything, does not
touch business logic. Reads the same Settings instance and the same
ProviderRegistry-held ResendProvider instance the real send path already
uses, plus the raw process environment (to catch env var names Settings
doesn't recognize at all, e.g. EMAIL_FROM / EMAIL_SEND_DRIVER).

Remove this file (and its registration in app/api/__init__.py and
app/main.py) once the Resend configuration issue is confirmed fixed.
"""

import os

from fastapi import APIRouter

from app.config.settings import get_settings
from app.providers import provider_registry, Channel

router = APIRouter(prefix="/api/debug", tags=["Debug"])

_ENV_KEYS_CHECKED = [
    "RESEND_API_KEY",
    "EMAIL_API_KEY",
    "EMAIL_FROM",
    "RESEND_FROM_EMAIL",
    "EMAIL_SENDER",
    "EMAIL_PROVIDER",
    "EMAIL_SEND_DRIVER",
]


@router.get("/resend-config")
async def get_resend_config():
    settings = get_settings()
    provider = provider_registry.get_provider(Channel.EMAIL)

    api_key = getattr(provider, "api_key", None) if provider else None
    from_email = getattr(provider, "from_email", None) if provider else None

    return {
        "api_key_present": bool(api_key),
        "from_email": from_email,
        "provider_name": type(provider).__name__ if provider else None,
        "driver": os.environ.get("JAWIS_EMAIL_PROVIDER", "jawis"),
        "all_env_keys_checked": {
            key: os.environ.get(key) is not None for key in _ENV_KEYS_CHECKED
        },
    }
