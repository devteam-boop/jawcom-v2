"""Gmail API reply-tracking sync.

Not part of app/jawis/ — JAWIS is the external CRM/lead-data client and has
no Gmail/email-reading code (verified before writing this module: no
existing "JAWIS Gmail sync" exists anywhere in this repository to reuse).
This is new code, using the pre-existing Google OAuth credentials already
present in Settings (GOOGLE_CLIENT_ID/SECRET/REFRESH_TOKEN, GMAIL_MONITOR_EMAIL).
"""
