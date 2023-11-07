"""
`utils.access_check` module: Flask route decorator checking for a valid access key.
"""
import uuid

from functools import wraps
from flask import g, request, jsonify


def access_check(to_decorate):
    """
    Flask route decorator checking for a valid access key.
    Access key must be provided via the "Access-Key" header.

    Executes the wrapped function is key is valid and has not been deactivated.

    Returns HTTP 401 if "Access-Key" header is missing.
    Returns HTTP 403 if access key does not exist / was disabled.
    Returns HTTP 400 if access key is in an invalid format.

    AccessKey object will be accessible in app context via g.access_key.
    """
    from ..models import AccessKey
    from flask import current_app

    @wraps(to_decorate)
    def decorated(*args, **kwargs):
        access_key_header = None
        access_key_digest = None
        access_key = None

        #
        # "Access-Key" / "access-key" header must be present
        #
        if "Access-Key" in request.headers:
            access_key_header = request.headers["Access-Key"]

        if "access-key" in request.headers:
            access_key_header = request.headers["access-key"]

        if not access_key_header:
            return jsonify({"error": "Missing Access-Key header."}), 401

        #
        # Access key must be an UUID v4
        #
        try:
            uuid.UUID(access_key_header, version=4)  # noqa
        except ValueError:
            return jsonify({"error": "Invalid access key format."}), 400

        #
        # Generate access key digest
        #
        try:
            access_key_digest = AccessKey.create_key_digest(
                key=access_key_header, salt=current_app.config["ACCESS_KEY_SALT"]
            )
            access_key_digest = access_key_digest[1]
        except ValueError:
            return jsonify({"error": "Invalid access key format."}), 400

        #
        # Access key must be present in the database and active
        #
        try:
            access_key = AccessKey.get(AccessKey.key_digest == access_key_digest)
        except AccessKey.DoesNotExist:
            return jsonify({"error": "Provided access key does not exist."}), 403

        if access_key.canceled_timestamp is not None:
            return jsonify({"error": "Provided access key was disabled."}), 403

        # Make access key object globally accessible for this context
        g.access_key = access_key

        return to_decorate(*args, **kwargs)

    return decorated
