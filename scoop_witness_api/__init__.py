"""
`scoop_witness_api` module: REST API for the `scoop-rest-api` project.
"""
import os

from flask import Flask

from scoop_witness_api import utils


def create_app(config_override: dict = {}):
    """
    App factory (https://flask.palletsprojects.com/en/2.3.x/patterns/appfactories/)
    config_override allows to replace app config values on an in-instance basis.
    """
    app = Flask(__name__)
    app.config.from_object("scoop_witness_api.config")

    # Handle config override
    if config_override and isinstance(config_override, dict):
        for key, value in config_override.items():
            if key in app.config:
                app.config[key] = value

    # Note: Every module in this app assumes the app context is available and initialized.
    with app.app_context():
        # Check that provided configuration is sufficient to run the app
        utils.config_check()

        # Create directory for TEMPORARY_STORAGE_PATH if it does not exist
        os.makedirs(app.config["TEMPORARY_STORAGE_PATH"], exist_ok=True)

        #
        # Import views
        #
        from scoop_witness_api import commands
        from scoop_witness_api import views

        return app
