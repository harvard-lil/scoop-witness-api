"""
Test suite for the "inspect-capture" command.
"""
import json


def test_inspect_capture_cli_invalid_id_capture(runner, id_capture):
    """inspect-capture command returns error code if id_capture is missing or invalid."""
    for args in ["", "--id_capture=foo", '--id_capture="9656592f-6821-49d6-9bcf-5e02aaff559e"']:
        result = runner.invoke(args=f"inspect-capture {args}")
        assert result.exit_code != 0


def test_inspect_capture_cli_valid_id_capture(runner, id_capture):
    """inspect-capture command returns capture info as JSON when given a valid id_capture."""
    from scoop_witness_api.models import Capture

    result = runner.invoke(args=f'inspect-capture --id_capture="{id_capture}"')

    capture_from_db = Capture.get(Capture.id_capture == id_capture)
    capture_from_cli = json.loads(result.output)

    assert result.exit_code == 0

    assert str(capture_from_db.id_capture) == capture_from_cli["id_capture"]
    assert capture_from_db.url == capture_from_cli["url"]
    assert capture_from_db.status == capture_from_cli["status"]
