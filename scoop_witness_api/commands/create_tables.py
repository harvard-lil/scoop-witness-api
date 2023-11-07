"""
`commands.create_tables` module: Controller for the `setup-database` CLI command.
"""
import click
from flask import current_app

from ..utils import get_db


@current_app.cli.command("create-tables")
def create_tables() -> None:
    """
    Initializes database for the Scoop REST API.
    Tables will be created only if they don't already exist.
    """
    from ..models import AccessKey, Capture

    click.echo("Creating tables...")
    get_db().create_tables([AccessKey, Capture])
    click.echo("Done.")
    exit(0)
