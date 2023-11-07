"""
`views.artifact` module: Provides regulated access to capture artifacts.
"""
import re
import os
import uuid
from pathlib import Path

from flask import jsonify, make_response, send_file, current_app


@current_app.route("/artifact/<id_capture>/<filename>")
def artifact_get(id_capture, filename):
    """
    [GET] /artifact/<id_capture>/<filename>
    Retrieves a specific artifact from a given capture.
    `id_capture` and `filename` params must be provided.

    Not behind auth.
    """
    full_path = None
    id_capture = str(id_capture)
    filename = str(filename)

    # Is id_capture an uuid?
    try:
        uuid.UUID(id_capture, version=4)  # noqa
    except ValueError:
        return jsonify({"error": "Invalid format for id_capture."}), 400

    # Is `filename` valid?
    # Can only be:
    # - "archive.wacz"
    # - "*.(pem|png|pdf|html|mp4|vtt)" (will be loaded from /attachments/ in that case)
    attachments_pattern = r"^[\w._-]+\.(pem|png|pdf|html|mp4|vtt)$"

    if filename != "archive.wacz" and not re.match(attachments_pattern, filename):
        return jsonify({"error": "Invalid filename provided."}), 400

    if re.match(attachments_pattern, filename):  # Prefix "attachments/" to the filename if needed
        filename = f"attachments{os.sep}{filename}"

    # Can the file be found?
    temporary_storage_path = current_app.config["TEMPORARY_STORAGE_PATH"]
    full_path = f"{temporary_storage_path}{os.sep}{id_capture}{os.sep}{filename}"
    full_path = Path(full_path).resolve()

    if not os.path.isfile(full_path):
        return jsonify({"error": "Requested file was not found."}), 404

    # Return file from storage
    response = make_response(send_file(full_path))
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"

    response.headers[
        "Access-Control-Expose-Headers"
    ] = "Content-Range, Content-Encoding, Content-Length"

    return response
