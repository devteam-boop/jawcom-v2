"""FastAPI dependencies for the application."""

from app.database.session import get_db

get_db_session = get_db
