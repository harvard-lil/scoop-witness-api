"""
Test suite for "views.artifact"
"""
import uuid

from flask import current_app


def test_artifact_get_misformatted_id_capture(client, access_key, default_artifact_filename):
    """[GET] /artifact returns HTTP 400 when provided with an id_capture in an invalid format."""
    access_key_readable = access_key["readable"]
    id_capture = "foo-bar-baz"

    response = client.get(
        f"/artifact/{id_capture}/{default_artifact_filename}",
        headers={"Access-Key": access_key_readable},
    )

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_artifact_get_invalid_id_capture(client, access_key, default_artifact_filename):
    """[GET] /artifact returns HTTP 404 when provided with an id_capture that does not exist."""
    access_key_readable = access_key["readable"]
    id_capture = str(uuid.uuid4())

    response = client.get(
        f"/artifact/{id_capture}/{default_artifact_filename}",
        headers={"Access-Key": access_key_readable},
    )

    assert response.status_code == 404
    assert "error" in response.get_json()


def test_artifact_get_misformatted_filename(client, access_key, id_capture):
    """[GET] /artifact returns HTTP 400 when provided with a filename in an invalid format."""
    access_key_readable = access_key["readable"]

    for filename in ["foo", "lorem.docx", "foo.wacz", 12, {}]:
        response = client.get(
            f"/artifact/{id_capture}/{filename}",
            headers={"Access-Key": access_key_readable},
        )

        assert response.status_code == 400
        assert "error" in response.get_json()


def test_artifact_get_invalid_filename(client, access_key, id_capture):
    """[GET] /artifact returns HTTP 404 when requested file was not found."""
    access_key_readable = access_key["readable"]

    for filename in ["archive.wacz", "screenshot.png"]:  # Do not exist since capture is pending
        response = client.get(
            f"/artifact/{id_capture}/{filename}",
            headers={"Access-Key": access_key_readable},
        )

        assert response.status_code == 404
        assert "error" in response.get_json()


def test_artifact_get_file(client, runner, access_key, id_capture):
    """[GET] /artifact returns HTTP 200 when requested file was found."""
    access_key_readable = access_key["readable"]

    # Run pending capture
    runner.invoke(args="start-capture-process --single-run")

    #
    # Try to access artifacts
    #
    for filename in ["archive.wacz", "screenshot.png"]:
        response = client.get(
            f"/artifact/{id_capture}/{filename}",
            headers={"Access-Key": access_key_readable},
        )

        assert response.status_code == 200
        assert response.headers["Access-Control-Allow-Origin"] == "*"
        assert response.headers["Access-Control-Allow-Headers"] == "*"
        assert response.headers["Access-Control-Allow-Methods"] == "*"
        assert "Content-Range" in response.headers["Access-Control-Expose-Headers"]
        assert "Content-Encoding" in response.headers["Access-Control-Expose-Headers"]
        assert "Content-Length" in response.headers["Access-Control-Expose-Headers"]
