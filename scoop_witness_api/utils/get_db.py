"""
`utils.get_db` module: Returns a connection to the database.
"""
import os

from peewee import MySQLDatabase
from playhouse.shortcuts import ReconnectMixin
from flask import current_app


class ReconnectMySQLDatabase(ReconnectMixin, MySQLDatabase):
    """
    Gives auto-reconnect capabilities to MySQLDatabase.
    https://github.com/coleifer/peewee/blob/master/playhouse/shortcuts.py#L211C7-L211C21
    """

    pass


def get_db() -> ReconnectMySQLDatabase:
    """
    Returns a database object.
    """
    with current_app.app_context():
        ssl = {}
        ca_path = current_app.config["DATABASE_CA_PATH"]

        # Use SSL cert if provided
        if ca_path and os.path.exists(ca_path):
            ssl = {"ca": ca_path, "check_hostname": True}

        return ReconnectMySQLDatabase(
            current_app.config["DATABASE_NAME"],
            user=current_app.config["DATABASE_USERNAME"],
            password=current_app.config["DATABASE_PASSWORD"],
            host=current_app.config["DATABASE_HOST"],
            port=int(current_app.config["DATABASE_PORT"]),
            ssl=ssl,
            autoconnect=True,
        )
