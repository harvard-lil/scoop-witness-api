"""
Test suite for "views.ping"
"""


def test_ping_get(client):
    """[GET] / returns HTTP 200 and an empty body."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.data == b""
