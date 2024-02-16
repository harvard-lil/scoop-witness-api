"""
`commands.status` module: Controller for the `status` CLI command.
"""

import click
from flask import current_app

from ..models import AccessKey, Capture


@current_app.cli.command("status")
def status() -> None:
    """
    Prints app status information:
    - List and status of access keys
    - Capture queue stats (pending, started)
    """
    captures = (
        Capture.select().where(Capture.status.in_(["pending", "started"])).order_by("id_capture")
    )
    captures_pending = 0
    captures_started = 0

    access_keys = AccessKey.select().order_by("id_access_key")

    click.echo(80 * "-")
    click.echo("Access keys:")
    click.echo(80 * "-")

    # Print report and index access keys by index
    for entry in access_keys:
        output = f"#{entry.id_access_key} "
        output += f"{entry.label} "
        output += f"created: {entry.created_timestamp} "

        if entry.canceled_timestamp:
            output += f"canceled: {entry.canceled_timestamp} "

        click.echo(output)

    click.echo(80 * "-")
    click.echo("Capture queue:")
    click.echo(80 * "-")
    for entry in captures:
        output = f"#{entry.id_capture} "
        output += f"author: {entry.id_access_key} "
        output += f"status: {entry.status} "
        output += f"created: {entry.created_timestamp} "

        if entry.started_timestamp:
            output += f"started: {entry.started_timestamp} "

        if entry.status == "pending":
            captures_pending += 1

        if entry.status == "started":
            captures_started += 1

    click.echo(f"-- {captures_pending} pending, {captures_started} started.")
