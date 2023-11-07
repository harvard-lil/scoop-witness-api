"""
Test suite for "views.capture"
"""
import uuid
import datetime

from flask import current_app


def test_capture_post_get_missing_access_key(client):
    """[POST|GET] /capture returns HTTP 401 if no Access-Key was provided."""
    response = client.post("/capture")
    assert response.status_code == 401
    assert "error" in response.get_json()


def test_capture_post_get_misformatted_access_key(client):
    """[POST|GET] /capture returns HTTP 400 if Access-Key is in an invalid format."""
    response = client.post("/capture", headers={"Access-Key": "foo-bar"})
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_capture_post_get_invalid_access_key(client, access_key):
    """[POST|GET] /capture returns HTTP 403 if Access-Key does not exist or has been disabled."""
    for verb in ["post", "get"]:
        endpoint = "/capture"

        if verb == "get":
            endpoint = "/capture/pretend-id-capture"

        #
        # Access key does not exist
        #
        response = getattr(client, verb)(endpoint, headers={"Access-Key": str(uuid.uuid4())})

        assert response.status_code == 403
        assert "error" in response.get_json()

        #
        # Access key has been disabled
        #
        access_key["instance"].canceled_timestamp = datetime.datetime.utcnow()
        access_key["instance"].save()

        response = getattr(client, verb)(endpoint, headers={"Access-Key": access_key["readable"]})

        assert response.status_code == 403
        assert "error" in response.get_json()


def test_capture_post_over_capacity(client, access_key, default_capture_url):
    """[POST] /capture returns HTTP 429 if there are too many captures in the queue."""
    access_key_readable = access_key["readable"]

    #
    # Create requests until we reach capacity
    #
    for i in range(0, current_app.config["MAX_PENDING_CAPTURES"]):
        response = client.post(
            "/capture",
            json={"url": default_capture_url},
            headers={"Access-Key": access_key_readable},
        )

        assert response.status_code == 200

    #
    # Next request must return HTTP 429
    #
    response = client.post(
        "/capture",
        json={"url": default_capture_url},
        headers={"Access-Key": access_key_readable},
    )

    assert response.status_code == 429
    assert "error" in response.get_json()


def test_capture_post_no_url(client, access_key):
    """[POST] /capture returns HTTP 400 if no capture URL is provided."""
    access_key_readable = access_key["readable"]

    response = client.post("/capture", headers={"Access-Key": access_key_readable}, json={})

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_capture_post_invalid_url(client, access_key):
    """[POST] /capture returns HTTP 400 if an invalid capture URL is provided."""
    access_key_readable = access_key["readable"]

    response = client.post(
        "/capture",
        headers={"Access-Key": access_key_readable},
        json={"url": "foo-bar-baz"},
    )

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_capture_post_invalid_callback_url(client, access_key, default_capture_url):
    """[POST] /capture returns HTTP 400 if an invalid callback URL is provided."""
    access_key_readable = access_key["readable"]

    response = client.post(
        "/capture",
        headers={"Access-Key": access_key_readable},
        json={"url": default_capture_url, "callback_url": "foo-bar-baz"},
    )

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_capture_post_save(client, access_key, default_capture_url):
    """[POST] /capture returns HTTP 200 and saves a capture request."""
    from scoop_witness_api.models import Capture

    access_key_readable = access_key["readable"]
    url = default_capture_url
    callback_url = default_capture_url + "callback"

    total_before_request = Capture.select().order_by("id_capture").count()

    response = client.post(
        "/capture",
        headers={"Access-Key": access_key_readable},
        json={"url": url, "callback_url": callback_url},
    )

    response_data = response.get_json()

    total_after_request = Capture.select().order_by("id_capture").count()

    assert total_after_request == total_before_request + 1
    assert response.status_code == 200
    assert "id_capture" in response_data
    assert response_data["url"] == url
    assert response_data["callback_url"] == callback_url
    assert response_data["status"] == "pending"


def test_capture_get_misformatted_id_capture(client, access_key):
    """[GET] /capture returns HTTP 400 when provided with an id_capture in an invalid format."""
    access_key_readable = access_key["readable"]
    id_capture = "foo-bar-baz"

    response = client.get(f"/capture/{id_capture}", headers={"Access-Key": access_key_readable})

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_capture_get_invalid_id_capture(client, access_key):
    """[GET] /capture returns HTTP 404 when provided with an id_capture that does not exist."""
    access_key_readable = access_key["readable"]
    id_capture = str(uuid.uuid4())

    response = client.get(f"/capture/{id_capture}", headers={"Access-Key": access_key_readable})

    assert response.status_code == 404
    assert "error" in response.get_json()


def test_capture_get_restricted_id_capture(client, access_key, default_capture_url):
    """[GET] /capture returns HTTP 403 when given an id_capture owned by a different user."""
    from scoop_witness_api.models import AccessKey

    restricted_id_capture = None

    #
    # Setup: create a distinct access key and make a capture using it
    #
    restricted_access_key_digest = AccessKey.create_key_digest(
        salt=current_app.config["ACCESS_KEY_SALT"]
    )

    AccessKey.create(label="Test", key_digest=restricted_access_key_digest[1])

    restricted_capture = client.post(
        "/capture",
        headers={"Access-Key": restricted_access_key_digest[0]},
        json={"url": default_capture_url},
    )

    restricted_id_capture = restricted_capture.get_json()["id_capture"]

    #
    # Try accessing that restricted record
    #
    access_key_readable = access_key["readable"]

    response = client.get(
        f"/capture/{restricted_id_capture}", headers={"Access-Key": access_key_readable}
    )

    assert response.status_code == 403
    assert "error" in response.get_json()


def test_capture_get_id_capture(client, runner, access_key, default_capture_url, id_capture):
    """[GET] /capture returns HTTP 200 when provided with a valid id_capture."""
    access_key_readable = access_key["readable"]

    # Check output before capture is run
    response = client.get(f"/capture/{id_capture}", headers={"Access-Key": access_key_readable})
    response_data = response.get_json()

    assert response.status_code == 200
    assert "id_capture" in response_data
    assert response_data["url"] == default_capture_url
    assert response_data["status"] == "pending"
    assert "stderr_logs" not in response_data
    assert "stdout_logs" not in response_data
    assert "scoop_capture_summary" not in response_data
    assert "artifacts" not in response_data

    # Run pending capture
    runner.invoke(args="start-capture-process --single-run")

    # Check response after capture is run
    response = client.get(f"/capture/{id_capture}", headers={"Access-Key": access_key_readable})
    response_data = response.get_json()

    assert response.status_code == 200
    assert "id_capture" in response_data
    assert response_data["url"] == default_capture_url
    assert response_data["status"] == "success"
    assert "stderr_logs" in response_data
    assert "stdout_logs" in response_data
    assert "scoop_capture_summary" in response_data
    assert "artifacts" in response_data
    assert len(response_data["artifacts"]) > 0
