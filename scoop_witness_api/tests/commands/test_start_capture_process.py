"""
Test suite for the "start-capture-process" command.
"""
import time
import os

from flask import current_app


def test_start_capture_process_cli(runner, access_key, id_capture):
    """start-process-capture command with --single-run flag runs a single capture, exit code 0."""
    from scoop_witness_api.models import Capture

    capture_before_run = Capture.get(Capture.id_capture == id_capture)
    capture_after_run = None

    # Process pending capture
    result = runner.invoke(args="start-capture-process --single-run")

    capture_after_run = Capture.get(Capture.id_capture == id_capture)

    assert result.exit_code == 0
    assert capture_before_run.id_capture == capture_after_run.id_capture
    assert capture_before_run.status != capture_after_run.status
    assert capture_before_run.ended_timestamp != capture_after_run.ended_timestamp
