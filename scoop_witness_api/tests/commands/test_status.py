"""
Test suite for the "status" command.
"""
import re


def test_status_cli(runner, access_key, id_capture):
    """status command returns statistics and exit code 0."""
    result = runner.invoke(args="status")

    # Check against known "default" state of test suite
    assert "Access keys:" in result.output
    assert (
        f"#{access_key['instance'].id_access_key} {access_key['instance'].label} created:"
        in result.output
    )

    assert "Capture queue:" in result.output
    assert "-- 1 pending, 0 started." in result.output

    # We expect the output to be 8 lines long because there is only 1 access key
    assert len(re.findall("\n", result.output)) == 8

    assert result.exit_code == 0
