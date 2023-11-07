"""
`views.ping` module: API health check route.
"""

from flask import current_app


@current_app.route("/")
def ping_get():
    """
    [GET] /
    Returns an empty HTTP 200 if the API is running.
    """
    return "", 200
