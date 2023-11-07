"""
`commands.cancel_access_key` module: Controller for the `cancel-access-key` CLI command.
"""
import datetime

import click
from flask import current_app


@current_app.cli.command("cancel-access-key")
@click.option("--id_access_key", required=True, type=int)
def cancel_access_key(id_access_key: int) -> None:
    """
    Cancels a given access key
    """
    from ..models import AccessKey

    id_access_key = int(id_access_key)

    if not id_access_key:
        click.echo("id_access_key is not in a valid format (integer).")
        exit(1)

    try:
        access_key = AccessKey.get(AccessKey.id_access_key == id_access_key)
    except AccessKey.DoesNotExist:
        click.echo(f"access key #{id_access_key} could not be found.")
        exit(1)

    if access_key.canceled_timestamp:
        click.echo(f"access key #{id_access_key} has already been canceled.")

    access_key.canceled_timestamp = datetime.datetime.utcnow()
    access_key.save()

    click.echo(f"access key #{id_access_key} canceled.")
