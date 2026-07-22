"""Sends the forgot-password OTP email — always to
settings.ADMIN_OTP_RECIPIENT_EMAIL, never to the requesting account.

Uses ResendProvider directly (app/providers/resend/resend_provider.py),
the same standalone provider class the codebase already documents as
"ready-to-use... Build only provider implementations" — this is exactly
that use case, not a Journey Engine/executor path, so it's called directly
rather than through IntegrationFactory/ExecutorFactory (which are wired
for journey nodes, not this).
"""

import logging
from datetime import datetime
from typing import Optional

from app.config.settings import get_settings
from app.providers.resend.resend_provider import ResendProvider

logger = logging.getLogger(__name__)


def _build_body(*, requester_name: str, requester_email: str, otp: str, ip_address: Optional[str], ttl_minutes: int) -> str:
    when = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    return (
        f"A password reset was requested for a JawCom admin account.\n\n"
        f"Requesting user: {requester_name} <{requester_email}>\n"
        f"Time: {when}\n"
        f"IP address: {ip_address or 'unknown'}\n\n"
        f"One-time code: {otp}\n"
        f"Valid for {ttl_minutes} minutes.\n\n"
        f"Relay this code to the requesting user only after verifying the request "
        f"came from them. If you did not expect this, no action is needed — the "
        f"code expires on its own and cannot be used without also knowing the "
        f"account's registered email."
    )


async def send_password_reset_otp(
    *,
    requester_name: str,
    requester_email: str,
    otp: str,
    ip_address: Optional[str],
) -> bool:
    settings = get_settings()
    provider = ResendProvider({})
    if not provider.is_configured():
        logger.error("Cannot send password-reset OTP: Resend is not configured (RESEND_API_KEY/from address)")
        return False

    body = _build_body(
        requester_name=requester_name,
        requester_email=requester_email,
        otp=otp,
        ip_address=ip_address,
        ttl_minutes=settings.ADMIN_OTP_TTL_MINUTES,
    )
    result = await provider.send_email(
        recipient=settings.ADMIN_OTP_RECIPIENT_EMAIL,
        subject=f"JawCom password reset code for {requester_email}",
        body=body,
    )
    if result.get("status") == "failed":
        logger.error("Password-reset OTP email failed to send: %s", result.get("error"))
        return False
    return True
