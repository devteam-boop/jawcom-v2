"""One-time/occasional admin bootstrap CLI — deliberately NOT an HTTP
endpoint (no bootstrap-token attack surface on a public route).

Usage (from backend/, with the venv active and DATABASE_URL set):

    python -m app.scripts.create_admin --email you@company.com --name "Your Name"

Prompts for the password interactively (getpass, never echoed, never in
shell history). Pass --password only for scripted/CI use — it will then
end up in shell history, so prefer the interactive prompt for real
accounts. Creates the account if the email doesn't exist yet, or updates
the password/name/role if it does (so this also doubles as a password-
reset tool an operator can run directly against the DB, bypassing the
OTP-to-mailbox flow entirely, for break-glass access).
"""

import argparse
import asyncio
import getpass
import sys

from sqlalchemy import select

from app.core.password_hashing import hash_password, validate_password_policy
from app.database.session import async_session_maker
from app.models.admin_user import AdminRole, AdminUser


async def _create_or_update(email: str, full_name: str, password: str, role: str) -> None:
    email = email.lower().strip()
    async with async_session_maker() as db:
        result = await db.execute(select(AdminUser).where(AdminUser.email == email))
        admin_user = result.scalar_one_or_none()

        if admin_user is None:
            admin_user = AdminUser(
                email=email,
                full_name=full_name,
                password_hash=hash_password(password),
                role=AdminRole(role),
                is_active=True,
            )
            db.add(admin_user)
            await db.commit()
            print(f"Created admin account: {email} (role={role})")
        else:
            admin_user.full_name = full_name
            admin_user.password_hash = hash_password(password)
            admin_user.role = AdminRole(role)
            admin_user.is_active = True
            admin_user.failed_login_attempts = 0
            admin_user.locked_until = None
            await db.commit()
            print(f"Updated existing admin account: {email} (role={role})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or reset a JawCom admin account")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True, dest="full_name")
    parser.add_argument("--role", default="admin", choices=[r.value for r in AdminRole])
    parser.add_argument("--password", default=None, help="Non-interactive only — prefer the prompt for real accounts")
    args = parser.parse_args()

    password = args.password or getpass.getpass("Password: ")
    confirm = args.password or getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Passwords do not match", file=sys.stderr)
        sys.exit(1)

    error = validate_password_policy(password)
    if error:
        print(f"Password rejected: {error}", file=sys.stderr)
        sys.exit(1)

    asyncio.run(_create_or_update(args.email, args.full_name, password, args.role))


if __name__ == "__main__":
    main()
