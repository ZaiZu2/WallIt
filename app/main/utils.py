from flask import abort
import time

from app import db

def wait_for_db(polling_interval: int = 3, timeout: int = 21) -> None:
    """Hotfix for fly.io database cluster not reviving fast enough after a period of inactivity."""
    for _ in range(timeout // polling_interval):
        try:
            db.session.execute("SELECT 1")
            return
        except Exception:
            time.sleep(3)

    abort(500, "Database is not available")
