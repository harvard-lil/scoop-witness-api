"""
`commands.create_access_key` module: Controller for the `create-access-key` CLI command.
"""
import click

from flask import current_app


@current_app.cli.command("create-access-key")
@click.option("--label", required=True, type=str)
def create_access_key(label: str) -> None:
    """
    Creates a API new access key. This key will only be displayed once.
    """
    from ..models import AccessKey

    # Check and filter --label
    label = str(label)
    label = label.replace("\r\n", " ")
    label = label.replace("\n", " ")
    label = label.strip()

    if not label:
        click.echo("Label must not be empty.")
        exit(1)

    # Generate a key and digest
    key = AccessKey.create_key_digest(salt=current_app.config["ACCESS_KEY_SALT"])

    # Store it
    access_key = AccessKey.create(label=label, key_digest=key[1])

    click.echo(f"Access key for user #{access_key.id_access_key} ({access_key.label}):")
    click.echo(key[0])
    click.echo("-- ⚠️ This key will never be displayed again")
