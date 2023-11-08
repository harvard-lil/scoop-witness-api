"""
`utils.get_db` module: Returns a connection to the database.
"""
import re
import os

from flask import g, current_app
import peewee


def get_db() -> peewee.SqliteDatabase:
    """
    Returns a connection to the database.
    - Creates it if not available.
    - Populates g.db
    - Uses the DATABASE_PATH and DATABASE_FILENAME environment variables.
    """
    with current_app.app_context():
        os.makedirs(current_app.config["DATABASE_PATH"], exist_ok=True)

        if not re.match(r"^[a-zA-Z0-9\-\_]+\.db$", current_app.config["DATABASE_FILENAME"]):
            raise NameError("DATABASE_FILENAME is invalid. Example: database12.db")

        db_fullpath = os.path.join(
            current_app.config["DATABASE_PATH"], current_app.config["DATABASE_FILENAME"]
        )

        g.db = peewee.SqliteDatabase(db_fullpath)

        try:
            assert g.db.connect(reuse_if_open=True)
        except AssertionError:
            raise ConnectionError(f"Could not connect to {db_fullpath}.")

        return g.db
