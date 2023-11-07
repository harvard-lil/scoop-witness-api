"""
`utils.config_check` module: Checks the app's config object.
"""
from flask import current_app


EXCLUDED_SCOOP_CLI_OPTIONS = [
    "--version",
    "-v" "--output",
    "-o",
    "--format",
    "-f",
    "--json-summary-output",
    "--export-attachments-output",
    "--intercepter",
    "--proxy-host",
    "--proxy-port",
    "--yt-dlp-path",
    "--crip-path",
]
""" List of Scoop CLI options which cannot be set at config level. """


def config_check() -> bool:
    """
    Checks the app's config object.
    Throws if properties are missing or unusable.
    Throws is no app context is available.
    """
    config = current_app.config

    # Check presence of required path-like / url-like properties
    for prop in ["TEMPORARY_STORAGE_PATH", "API_DOMAIN", "API_STORAGE_URL"]:
        if prop not in config:
            raise Exception(f"config object must contain a {prop} property")

        if not isinstance(config[prop], str):
            raise Exception(f"{prop} config property must be a string")

    # Check SCOOP_CLI_OPTIONS
    if "SCOOP_CLI_OPTIONS" not in config or not isinstance(config["SCOOP_CLI_OPTIONS"], dict):
        raise Exception("config object must contain a SCOOP_CLI_OPTIONS dictionary.")

    for key, value in config["SCOOP_CLI_OPTIONS"].items():
        if not key.startswith("--"):
            raise Exception(f"config: {key} is not a valid property of SCOOP_CLI_OPTIONS.")

        if key.lower() in EXCLUDED_SCOOP_CLI_OPTIONS:
            raise Exception(f"Scoop CLI option {key} cannot be set at config level.")

    # Misc (just check presence)
    for prop in [
        "DATABASE_USERNAME",
        "DATABASE_PASSWORD",
        "DATABASE_HOST",
        "DATABASE_PORT",
        "DATABASE_NAME",
        "MAX_PENDING_CAPTURES",
        "EXPOSE_SCOOP_LOGS",
        "TEMPORARY_STORAGE_EXPIRATION",
        "PROCESSES",
        "PROCESSES_PROXY_PORT",
        "ACCESS_KEY_SALT",
        "SCOOP_TIMEOUT_FUSE",
    ]:
        if prop not in config:
            raise Exception(f"config object must define {prop}.")

    return True
