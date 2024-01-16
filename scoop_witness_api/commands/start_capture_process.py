"""
`commands.start_capture_process` module: Controller for the `start-capture-process` CLI command.
"""
import os
import time
import datetime
import subprocess
import random
import traceback
import json

import requests
import click
from flask import current_app, jsonify

from ..utils import capture_to_dict


@current_app.cli.command("start-capture-process")
@click.option("--proxy-port", required=False, default=9000)
@click.option("--single-run", is_flag=True, required=False, default=False)
def start_capture_process(proxy_port=9000, single_run=False) -> None:
    """
    Takes a capture from the queue and processes it.
    Runs in a loop unless interrupted, or if "--single-run" is on.
    Multiple instances of this command can be run in parallel: see "start-capture-process" command.

    If interrupted during capture: puts capture back into queue.
    """
    from ..models import Capture

    if not proxy_port or proxy_port > 65535:
        click.echo("--proxy-port must be a valid, free TCP port.")
        exit(1)

    while True:
        try:
            captures = None
            """ List of pending captures. """

            capture = None
            """ Capture currently being processed. """

            proxy_port_is_available = True
            """ Determines if the targeted proxy port is currently available.
                Capture cycle will be skipped if not. """

            storage_path = None
            """ Path to temporary folder used by the API to store artifacts.
                Will be created on the fly if necessary. """

            attachments_path = None
            """ Path to the temporary folder used by the API to store attachments.
                Will be created on the fly if necessary. """

            archive_path = None
            """ Path to the resulting WARC/WACZ file. Should be a filename under storage_path. """

            json_summary_path = None
            """ Path to the JSON summary file. Should be a filename under storage_path. """

            scoop_options = current_app.config["SCOOP_CLI_OPTIONS"]
            """ Shortcut to app-level Scoop CLI options. """

            scoop_exit_code = None
            """ Exit code from Scoop run. """

            #
            # Pull 1 pending capture from the queue
            #
            captures = (
                Capture.select()
                .where(Capture.status == "pending")
                .order_by("created_timestamp")
                .paginate(1, 1)
            )

            #
            # If there is a capture to process:
            # Check that --proxy-port is available
            #
            if len(captures):
                try:
                    requests.head(f"http://localhost:{proxy_port}", timeout=1)
                    proxy_port_is_available = False
                except requests.exceptions.ReadTimeout:
                    proxy_port_is_available = False
                except Exception:
                    proxy_port_is_available = True

                if not proxy_port_is_available:
                    click.echo(f"{log_prefix()} Port {proxy_port} already in use - skipping cycle")

            #
            # Wait until next tick if no capture to process or port is not available.
            #
            if not len(captures) or not proxy_port_is_available:
                if single_run:
                    break
                else:
                    # Randomize wait time to prevent queuing clashes (TBD)
                    time.sleep(0.5 + random.random())
                    continue

            capture = captures[0]

            #
            # Define paths
            #

            # Temporary storage folder
            temporary_storage_path = current_app.config["TEMPORARY_STORAGE_PATH"]
            storage_path = f"{temporary_storage_path}{os.sep}{capture.id_capture}"
            json_summary_path = f"{storage_path}{os.sep}archive.json"
            attachments_path = f"{storage_path}{os.sep}attachments"
            archive_path = f"{storage_path}{os.sep}archive.wacz"

            #
            # Mark capture as "started"
            #
            update_count = (
                Capture.update(status="started")
                .where(Capture.id_capture == capture.id_capture, Capture.status == "pending")
                .execute()
            )
            # https://github.com/harvard-lil/perma/blob/develop/perma_web/perma/models.py#L2115C1-L2118C18

            if update_count < 1:
                click.echo(
                    f"{log_prefix(capture)} Already running in another process: status already updated."  # noqa
                )
                continue

            # Get a fresh copy of the capture job
            capture = Capture.get(Capture.id_capture == capture.id_capture)
            capture.started_timestamp = datetime.datetime.utcnow()
            capture.save()

            click.echo(f"{log_prefix(capture)} Marked as started")

            #
            # Create capture-specific folders
            #
            os.makedirs(storage_path)
            click.echo(f"{log_prefix(capture)} Temporary storage folder: {storage_path}")
            os.makedirs(attachments_path)

            #
            # Run capture
            #
            scoop_args = [
                "npx",
                "scoop",
                capture.url,
                "--output",
                archive_path,
                "--format",
                "wacz",
                "--json-summary-output",
                json_summary_path,
                "--export-attachments-output",
                attachments_path,
                "--proxy-port",
                str(proxy_port),
            ]

            for key, value in scoop_options.items():
                scoop_args.append(key)
                scoop_args.append(str(value))

            process = subprocess.run(
                scoop_args,
                capture_output=True,
                text=True,
                timeout=scoop_options["--capture-timeout"] / 1000
                + int(current_app.config["SCOOP_TIMEOUT_FUSE"]),
            )

            scoop_exit_code = process.returncode
            capture.stdout_logs = process.stdout
            capture.stderr_logs = process.stderr

            #
            # Check capture results
            #

            # Assume capture failed until proven otherwise
            capture.status = "failed"
            capture.ended_timestamp = datetime.datetime.utcnow()
            success = False
            failed_reason = ""

            if scoop_exit_code != 0:
                failed_reason = f"exit code {scoop_exit_code}"

            # Confirm capture success
            if scoop_exit_code == 0:
                success = True

                # Archive file must exist
                if not os.path.exists(archive_path):
                    failed_reason = f"{archive_path} not found"
                    success = False

                # JSON summary must exist
                if not os.path.exists(json_summary_path) and not failed_reason:
                    failed_reason = f"{json_summary_path} not found"
                    success = False

                # Analyze JSON summary and:
                # - Check that expected extracted attachments are indeed on disk
                # - Store a copy of the summary in the database
                if success:
                    with open(json_summary_path) as file:
                        json_summary = json.load(file)
                        filenames_to_check = []

                        capture.summary = json_summary  # Store copy of JSON summary

                        for filename in json_summary["attachments"].values():
                            if isinstance(filename, list):  # Example: "certificates" is a list
                                filenames_to_check = filenames_to_check + filename
                            else:
                                filenames_to_check.append(filename)

                        for filename in filenames_to_check:
                            filepath = f"{attachments_path}{os.sep}{filename}"
                            if not os.path.exists(filepath):
                                click.echo(f"{log_prefix(capture)} Failed ({filepath} not found)")
                                success = False

            # Report on status and update database record
            if success:
                click.echo(f"{log_prefix(capture)} Success")
                capture.status = "success"
            else:
                click.echo(f"{log_prefix(capture)} Failed ({failed_reason})")
                capture.status = "failed"

            capture.save()

            #
            # Break loop if we are in single-run mode
            #
            if single_run:
                break

        #
        # Edge case: Scoop keeps running more than SCOOP_TIMEOUT_FUSE seconds after capture:
        # Process timeout has been reached
        #
        except subprocess.TimeoutExpired:
            if capture:
                capture.status = "failed"
                capture.ended_timestamp = datetime.datetime.utcnow()
                capture.save()
                click.echo(f"{log_prefix(capture)} Failed (timeout violation)")

        #
        # Catch-all
        #
        except Exception:
            if capture:
                capture.status = "failed"
                capture.ended_timestamp = datetime.datetime.utcnow()
                capture.save()
                click.echo(f"{log_prefix(capture)} Failed (other, see logs)")

            click.echo(traceback.format_exc())  # Full trace should be in the logs
            break  # Close the loop and terminate process
        #
        # Voluntary interruption
        #
        except:  # noqa: we can't intercept interrupt signals if we specify an exception type
            click.echo("Operation aborted")

            if capture:
                if capture.status != "failed":
                    capture.status = "failed"

                capture.ended_timestamp = datetime.datetime.utcnow()
                capture.save()  # Update capture state

            break
        #
        # In any case: call webhook, if any
        #
        finally:
            if capture and capture.callback_url:
                try:
                    click.echo(f"{log_prefix(capture)} Callback to {capture.callback_url}")

                    # Workaround to be able to use Flask's jsonify, for consistency across the app
                    json_data = json.loads(jsonify(capture_to_dict(capture)).data.decode("utf-8"))

                    requests.post(capture.callback_url, json=json_data, timeout=10)
                except Exception:
                    click.echo(f"{log_prefix(capture)} Callback to {capture.callback_url} failed")
                    click.echo(traceback.format_exc())  # Full trace should be in the logs


def log_prefix(capture=None) -> str:
    """Returns a log prefix to be added at the beginning of each line."""
    timestamp = datetime.datetime.utcnow().isoformat(sep="T", timespec="auto")

    if capture:
        return f"[{timestamp}] Capture #{capture.id_capture} |"
    else:
        return f"[{timestamp}] (Pre-capture) |"
