""" Test suite configuration and fixtures. """
import uuid
import os
from tempfile import TemporaryDirectory

import pytest
import pymysql
from dotenv import load_dotenv

from scoop_witness_api import create_app

load_dotenv()


@pytest.fixture(scope="session")
def app():
    """
    Creates a test-specific app context as well as a dedicated database for this test suite.

    Default test credentials can be replaced using environment variables:
    - TESTS_DATABASE_HOST
    - TESTS_DATABASE_USERNAME
    - TESTS_DATABASE_PASSWORD
    - TESTS_DATABASE_PORT
    """
    with TemporaryDirectory() as temporary_dir:
        DATABASE_HOST = "127.0.0.1"
        DATABASE_USERNAME = "root"
        DATABASE_PASSWORD = ""
        DATABASE_PORT = 3306
        DATABASE_NAME = str(uuid.uuid4())
        TEMPORARY_STORAGE_PATH = temporary_dir

        # Default test credentials can be replaced using environment variables.
        if "TESTS_DATABASE_HOST" in os.environ:
            DATABASE_HOST = os.environ["TESTS_DATABASE_HOST"]

        if "TESTS_DATABASE_USERNAME" in os.environ:
            DATABASE_USERNAME = os.environ["TESTS_DATABASE_USERNAME"]

        if "TESTS_DATABASE_PASSWORD" in os.environ:
            DATABASE_PASSWORD = os.environ["TESTS_DATABASE_PASSWORD"]

        if "TESTS_DATABASE_PORT" in os.environ:
            DATABASE_PORT = int(os.environ["TESTS_DATABASE_PORT"])

        # Create temporary database
        db = pymysql.connect(
            host=DATABASE_HOST,
            user=DATABASE_USERNAME,
            passwd=DATABASE_PASSWORD,
            port=DATABASE_PORT,
        )

        db.cursor().execute(
            f"CREATE DATABASE `{DATABASE_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;"
        )

        # Create app context
        app = create_app(
            {
                "DATABASE_USERNAME": DATABASE_USERNAME,
                "DATABASE_PASSWORD": DATABASE_PASSWORD,
                "DATABASE_HOST": DATABASE_HOST,
                "DATABASE_PORT": DATABASE_PORT,
                "DATABASE_NAME": DATABASE_NAME,
                "DATABASE_CA_PATH": "",
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

        # Drop database once test session is complete
        #
        # Note: This won't run if the test suite crashes.
        # This gives us the opportunity to inspect the database that was used during the crash.
        # This is TBD -- we can also cleanup on crash.
        db.cursor().execute(f"DROP SCHEMA `{DATABASE_NAME}`;")
        db.close()


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
