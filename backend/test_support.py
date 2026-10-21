"""Shared helpers for the backend test suites.

Importing this module (or the ``isolate_db`` helper below) redirects the whole
application at a throwaway SQLite file so a test run can never delete rows from
the real development database.

Usage::

    from test_support import isolate_db
    isolate_db()          # must run BEFORE importing app/database modules
"""

import os
import tempfile


def isolate_db(prefix="ss3_test_"):
    """Point SS3_DB_PATH at a fresh temp database and return its path.

    Call this before importing ``app`` / ``database`` so every module that
    captures the path at import time uses the temp file.
    """
    fd, path = tempfile.mkstemp(prefix=prefix, suffix=".db")
    os.close(fd)
    os.environ["SS3_DB_PATH"] = path
    return path


def cleanup_db(path):
    """Delete a temporary database file, ignoring errors."""
    try:
        os.remove(path)
    except OSError:
        pass
