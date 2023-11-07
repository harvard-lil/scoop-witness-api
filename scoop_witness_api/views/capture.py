"""
`views.capture` module: /capture routes.
"""
import uuid

from flask import request, jsonify, g, current_app
import validators

from ..utils import access_check
from ..models import Capture
from ..utils import capture_to_dict


@current_app.route("/capture", methods=["POST"])
@access_check
def capture_post():
    """
    [POST] /capture
    Creates a capture request.

    Behind auth: Requires Access-Key header (see utils.access_check).

    Accepts JSON body with the following properties:
    - "url": Url to capture (required)
    - "callback_url": POST URL to be called upon completion (optional)

    Returns HTTP 200 and a JSON object containing user-facing capture information.
    Returns HTTP 429 if MAX_PENDING_CAPTURES is exceeded.
    """
    input = request.get_json()
    url = None
    callback_url = None
    MAX_PENDING_CAPTURES = current_app.config["MAX_PENDING_CAPTURES"]

    #
    # Check if there is remaining capacity
    #
    pending_captures_count = Capture.select().where(Capture.status == "pending").count()

    if pending_captures_count >= MAX_PENDING_CAPTURES:
        return jsonify({"error": "Capture server is over capacity."}), 429

    #
    # Required input: url
    #
    if "url" not in input:
        return jsonify({"error": "No URL provided."}), 400

    if validators.url(input["url"]) is not True:
        return jsonify({"error": "Provided URL is not valid."}), 400

    url = input["url"]

    #
    # Optional input: callback url
    #
    if "callback_url" in input:
        if validators.url(input["callback_url"]) is not True:
            return jsonify({"error": "Provided callback URL is not valid."}), 400

        callback_url = input["callback_url"]

    #
    # Create capture request
    #
    capture = Capture()
    capture.url = url

    if callback_url:
        capture.callback_url = callback_url

    capture.id_access_key = g.access_key.id_access_key

    try:
        capture.save(force_insert=True)
    except Exception as err:
        current_app.logger.error(err)
        return jsonify({"error": "Could not create capture request."}), 500

    #
    # Return info
    #
    return jsonify(capture_to_dict(capture)), 200


@current_app.route("/capture/<id_capture>", methods=["GET"])
@access_check
def capture_get(id_capture):
    """
    [GET] /capture/<id_capture>
    Returns information about a given capture, identified by `id_capture`.

    Behind auth: Requires Access-Key header (see utils.access_check).

    Will only return information if the capture is associated with the access key that was provided.
    """
    capture = None

    # Is id_capture an uuid?
    try:
        uuid.UUID(id_capture, version=4)  # noqa
    except ValueError:
        return jsonify({"error": "Invalid format for id_capture."}), 400

    # Get capture object from database
    try:
        capture = Capture.get_by_id(id_capture)
    except Capture.DoesNotExist:
        return jsonify({"error": "No match for given id_capture."}), 404

    # Is the currently logged-in user the owner of this capture?
    if capture.id_access_key.id_access_key != g.access_key.id_access_key:
        return jsonify({"error": "Access to this capture was denied."}), 403

    return jsonify(capture_to_dict(capture)), 200
