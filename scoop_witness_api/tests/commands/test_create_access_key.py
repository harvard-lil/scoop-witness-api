"""
Test suite for the "create-access-key" command.
"""
import uuid


def test_create_access_key_cli_invalid_label(runner, access_key):
    """create-access-key command returns error code if label is missing."""
    from scoop_witness_api.models import AccessKey

    total_access_keys_before = 1
    total_access_keys_after = None

    result = runner.invoke(args="create-access-key")
    assert result.exit_code != 0

    # Make sure no access_key has been created
    total_access_keys_after = AccessKey.select().count()

    assert total_access_keys_before == total_access_keys_after


def test_create_access_key_cli_valid_label(runner, access_key):
    """create-access-key command creates an access key and prints it when given a valid label."""
    from scoop_witness_api.models import AccessKey

    new_access_key_label = "This is a test"
    new_access_key = None

    result = runner.invoke(args=f'create-access-key --label="{new_access_key_label}"')

    assert result.exit_code == 0

    # Make sure access_key has been created and is operational
    new_access_key = AccessKey.get(AccessKey.label == new_access_key_label)
    assert new_access_key
    assert new_access_key.canceled_timestamp is None

    # Make sure access_key has been shown to user
    assert new_access_key_label in result.output
    assert uuid.UUID(result.output.split("\n")[1], version=4)  # Throws if not UUID
