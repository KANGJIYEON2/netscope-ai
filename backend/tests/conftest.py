"""Shared fixtures for backend tests."""
import os

# Provide a dummy DATABASE_URL so that imports don't crash at module level.
# Tests that actually hit the DB should override this with a real URL.
os.environ.setdefault("DATABASE_URL", "sqlite:///")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest")
os.environ.setdefault("FRONTEND_ORIGIN", "http://localhost:3000")
