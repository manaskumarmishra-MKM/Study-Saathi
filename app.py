"""Application entry point for StudySaathi.

This light wrapper keeps the root app importable while delegating to the backend
implementation used by the project.
"""

from backend.app import app


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
