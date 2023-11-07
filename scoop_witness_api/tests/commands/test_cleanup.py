"""
Test suite for the "cleanup" command.
"""
import time
import os

from flask import current_app


def test_cleanup_cli(runner, access_key, id_capture):
    """cleanup command deletes obsolete files and returns exit code 0."""

    before_cleanup = 0
    after_cleanup = 0

    def count_dirs():
        """Counts total of dirs present in temporary storage + Scoop's "tmp" folder."""
        dirs = 0
        dirs += len(os.listdir(current_app.config["TEMPORARY_STORAGE_PATH"]))
        dirs += len(os.listdir(f"node_modules{os.sep}@harvard-lil{os.sep}scoop{os.sep}tmp"))
        return dirs

    # Process pending capture
    runner.invoke(args="start-capture-process --single-run")

    # Count number of dirs in storage
    before_cleanup = count_dirs()

    # Wait for until expiration time is reached
    time.sleep(current_app.config["TEMPORARY_STORAGE_EXPIRATION"])

    result = runner.invoke(args="cleanup")
    after_cleanup = count_dirs()

    assert before_cleanup != after_cleanup
    assert after_cleanup == 0
    assert result.exit_code == 0
