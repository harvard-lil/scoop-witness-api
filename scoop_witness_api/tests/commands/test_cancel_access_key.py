"""
Test suite for the "cancel-access-key" command.
"""


def test_cancel_access_key_cli_invalid_id_access_key(runner, access_key):
    """cancel-access-key command returns error code if id_access_key is missing or invalid."""
    from scoop_witness_api.models import AccessKey

    for args in ["", "--id_access_key=foo", "--id_access_key=42"]:
        result = runner.invoke(args=f"cancel-access-key {args}")
        assert result.exit_code != 0

        # Make sure access_key hasn't been altered
        access_key["instance"] = AccessKey.get(
            AccessKey.id_access_key == access_key["instance"].id_access_key
        )

        assert access_key["instance"].canceled_timestamp is None


def test_cancel_access_key_cli_valid_id_access_key(runner, access_key):
    """cancel-access-key command returns success exit code if id_access_key is valid."""
    from scoop_witness_api.models import AccessKey

    id_access_key = access_key["instance"].id_access_key

    result = runner.invoke(args=f"cancel-access-key --id_access_key={id_access_key}")
    assert result.exit_code == 0

    # Make sure access_key has been canceled
    access_key["instance"] = AccessKey.get(AccessKey.id_access_key == id_access_key)

    assert access_key["instance"].canceled_timestamp is not None
