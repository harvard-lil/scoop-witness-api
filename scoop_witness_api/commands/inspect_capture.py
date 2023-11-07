"""
`commands.inspect-capture` module: Controller for the `inspect-capture` CLI command.
"""
import uuid

from flask import json
import click
from flask import current_app

from ..models import Capture


@current_app.cli.command("inspect-capture")
@click.option("--id_capture", required=True, type=str)
def inspect_capture(id_capture: int) -> None:
    """
    Returns the full details of a given capture as JSON, if found.
    """
    capture = None

    # Is id_capture an uuid?
    try:
        uuid.UUID(id_capture, version=4)  # noqa
    except ValueError:
        click.echo("Invalid format for id_capture.")

    try:
        capture = Capture.get(Capture.id_capture == id_capture)
    except Capture.DoesNotExist:
        click.echo(f"Capture #{id_capture} could not be found.")
        exit(1)

    # Note: we do not use utils.capture_to_dict here.
    # This is because we want a full report, including logs, regardless of capture state.
    click.echo(
        json.dumps(
            {
                "id_capture": capture.id_capture,
                "id_access_key": int(str(capture.id_access_key)),
                "url": capture.url,
                "callback_url": capture.callback_url,
                "status": capture.status,
                "created_timestamp": capture.created_timestamp,
                "started_timestamp": capture.started_timestamp,
                "ended_timestamp": capture.ended_timestamp,
                "stdout_logs": capture.stdout_logs,
                "stderr_logs": capture.stderr_logs,
                "summary": capture.summary,
            }
        )
    )
