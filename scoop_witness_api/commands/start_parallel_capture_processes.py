"""
`commands.start_parallel_capture_processes` module:
Controller for the `start-parallel-capture-processes` CLI command.
"""
import sys
import time
import datetime
import subprocess
import signal

import click

from flask import current_app


@current_app.cli.command("start-parallel-capture-processes")
def start_parallel_capture_processes() -> None:
    """
    Runs multiple capture processes in parallel.

    Use SIGINT (Ctrl + C) to interrupt.

    See configuration options in config.py.
    """
    PROCESSES = int(current_app.config["PROCESSES"])

    processes = []

    #
    # Start capture processes
    #
    for process_index in range(0, PROCESSES):
        process = start_capture_process(process_index)
        processes.append(process)

    #
    # Process loop
    #
    try:
        while True:
            time.sleep(1)  # Waiting for SIGINT

            # Try to restart processes that crashed
            for process_index, process in enumerate(processes):
                exit_code = process.poll()

                if exit_code is not None:
                    if exit_code > 0:
                        click.echo(f"{log_prefix(process_index)} crashed - Rebooting")
                    else:
                        click.echo(f"{log_prefix(process_index)} stopped - Rebooting")

                    processes[process_index] = start_capture_process(process_index)

    #
    # Voluntary interruption
    #
    except:  # noqa: we can't intercept interrupt signals if we specify an exception type
        click.echo("Operation aborted")

        for process_index, process in enumerate(processes):
            process.send_signal(signal.SIGINT)
            process.wait()
            click.echo(f"{log_prefix(process_index)} Received SIGINT signal.")


def start_capture_process(process_index: int) -> subprocess.Popen:
    """Starts a capture process on port PROCESSES_PROXY_PORT + process_index."""
    PROCESSES_PROXY_PORT = int(current_app.config["PROCESSES_PROXY_PORT"])

    port = PROCESSES_PROXY_PORT + process_index

    # Wait 1 second before launching each process.
    # NOTE: This is a stretch to fit into "barebones" philosophy of the project. TBD.
    time.sleep(1)

    process = subprocess.Popen(
        ["flask", "start-capture-process", "--proxy-port", str(port)],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    click.echo(f"{log_prefix(process_index)} Launched on port {port}")

    return process


def log_prefix(process_index: int) -> str:
    """Returns a log prefix to be added at the beginning of each line."""
    timestamp = datetime.datetime.utcnow().isoformat(sep="T", timespec="auto")
    return f"[{timestamp}] Process #{process_index} |"
