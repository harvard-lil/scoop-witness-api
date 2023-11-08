""" Test suite configuration and fixtures. """
import uuid
import os
from tempfile import TemporaryDirectory

import pytest

from scoop_witness_api import create_app


@pytest.fixture(scope="session")
def app():
    """
    Creates a test-specific app context as well as a dedicated database for this test suite.
    """
    with TemporaryDirectory() as temporary_dir:
        DATABASE_PATH = os.path.join(temporary_dir, "database")
        TEMPORARY_STORAGE_PATH = os.path.join(temporary_dir, "storage")
        DATABASE_FILENAME = f"{uuid.uuid4()}.db"

        os.makedirs(TEMPORARY_STORAGE_PATH, exist_ok=True)
        os.makedirs(DATABASE_FILENAME, exist_ok=True)

        # Create app context
        app = create_app(
            {
                "DATABASE_PATH": DATABASE_PATH,
                "DATABASE_FILENAME": DATABASE_FILENAME,
                "MAX_PENDING_CAPTURES": 5,
                "EXPOSE_SCOOP_LOGS": True,
                "EXPOSE_SCOOP_CAPTURE_SUMMARY": True,
                "TEMPORARY_STORAGE_PATH": TEMPORARY_STORAGE_PATH,
                "TEMPORARY_STORAGE_EXPIRATION": 3,
            }
        )

        # Create tables
        with app.app_context():
            from scoop_witness_api.utils import get_db
            from scoop_witness_api.models import AccessKey, Capture

            get_db().create_tables([AccessKey, Capture])

        # Run tests
        yield app


@pytest.fixture(autouse=True)
def database_cleanup(app):
    """
    Clear leftover records before each test.
    """
    with app.app_context():
        from scoop_witness_api.models import AccessKey, Capture

        Capture.delete().execute()
        AccessKey.delete().execute()

        yield


@pytest.fixture()
def access_key(app) -> dict:
    """
    Creates, stores and return an access key for the current test.
    Returned dict contains an AccessKey object and the human-readable access key.
    """
    with app.app_context():
        from scoop_witness_api.models import AccessKey

        access_key_digest = AccessKey.create_key_digest(salt=app.config["ACCESS_KEY_SALT"])
        access_key = AccessKey.create(label="Test", key_digest=access_key_digest[1])
        access_key_readable = access_key_digest[0]

    return {"instance": access_key, "readable": access_key_readable}


@pytest.fixture()
def client(app):
    """Returns a Flask HTTP test client for the current app."""
    return app.test_client()


@pytest.fixture()
def runner(app):
    """Returns a Flask CLI test client for the current app."""
    return app.test_cli_runner()


@pytest.fixture()
def default_capture_url() -> str:
    return "https://example.com"


@pytest.fixture()
def default_artifact_filename() -> str:
    return "archive.wacz"


@pytest.fixture()
def id_capture(app, client, access_key, default_capture_url) -> str:
    """
    Creates a capture request for the default capture URL.
    This means that every test will have a pending capture in the queue.
    Returns id_capture.
    """
    with app.app_context():
        from scoop_witness_api.models import Capture

        capture = client.post(
            "/capture",
            headers={"Access-Key": access_key["readable"]},
            json={"url": default_capture_url},
        )

        return capture.get_json()["id_capture"]
