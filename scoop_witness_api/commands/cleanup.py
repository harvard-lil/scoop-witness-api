"""
`commands.cleanup` module: Controller for the `cleanup` CLI command.
"""
import os
import glob
import re
import datetime
import shutil

import click
from flask import current_app


@current_app.cli.command("cleanup")
def cleanup() -> None:
    """
    Clears temporarily storage of expired files.
    """
    #
    # API temporary storage folder
    #
    TEMPORARY_STORAGE_PATH = current_app.config["TEMPORARY_STORAGE_PATH"]
    TEMPORARY_STORAGE_EXPIRATION = int(current_app.config["TEMPORARY_STORAGE_EXPIRATION"])

    for directory in glob.glob(f"{TEMPORARY_STORAGE_PATH}{os.sep}*"):
        # Directory must be a UUID
        if not re.search(
            r"[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12}$", directory
        ):
            continue

        # Directory must have been created more than TEMPORARY_STORAGE_EXPIRATION seconds ago
        diff = datetime.datetime.now().timestamp() - os.stat(directory).st_mtime

        if diff >= TEMPORARY_STORAGE_EXPIRATION:
            click.echo(f"{directory} has expired and will be deleted")
            shutil.rmtree(directory)

    #
    # Scoop's temporary folder, in case there are lingering files there.
    #
    SCOOP_TMP_PATH = f"node_modules{os.sep}@harvard-lil{os.sep}scoop{os.sep}tmp"

    for directory in glob.glob(f"{SCOOP_TMP_PATH}{os.sep}*"):
        # Directory must have been created more than TEMPORARY_STORAGE_EXPIRATION seconds ago
        diff = datetime.datetime.now().timestamp() - os.stat(directory).st_mtime

        if diff >= TEMPORARY_STORAGE_EXPIRATION:
            click.echo(f"{directory} has expired and will be deleted")
            shutil.rmtree(directory)
