"""
`config` module: App-wide settings, example file. Duplicate as config.py.

If you would like to use an alternative way of providing configuration, see:
- https://flask.palletsprojects.com/en/2.3.x/config/#configuring-from-data-files
- https://flask.palletsprojects.com/en/2.3.x/config/#configuring-from-environment-variables
... and update __init__.py accordingly.
"""

#
# Security settings
#
ACCESS_KEY_SALT = b"$2b$12$rXmm9AWx82fxw9Jbs1PXI.zebeXu4Ydi1huwxyH5k9flyhccBBTxa"  # default / dev
""" Salt to be used to hash access keys. """

MAX_PENDING_CAPTURES = 300
""" Stop accepting new capture requests if there are over X captures in the queue. """

EXPOSE_SCOOP_LOGS = False
""" If `True`, Scoop logs will be exposed at API level by capture_to_dict. Handle with care. """

EXPOSE_SCOOP_CAPTURE_SUMMARY = True
""" If `True`, Scoop's capture summary will be exposed at API level via capture_to_dict. Handle with care. """  # noqa

#
# Database settings
#
DATABASE_PATH = "./database"
""" (SQLite) Database storage path. """

DATABASE_FILENAME = "scoop.db"
""" (SQLite) Database filename. """

#
# Paths settings
#
TEMPORARY_STORAGE_PATH = "./storage"
""" Directory in which files will be (temporarily) stored. """

TEMPORARY_STORAGE_EXPIRATION = 60 * 60 * 24
""" How long should temporary files be stored for? (In seconds). Can be provided via an environment variable. """  # noqa


#
# API-wide settings
#
API_DOMAIN = "http://localhost:5000"
""" Root URL of the API. """

API_STORAGE_URL = f"{API_DOMAIN}/storage"
""" URL for the storage folder. """

#
# Background processing options
#
PROCESSES = 6
""" How many tick commands (capture processing) should run in parallel."""

PROCESSES_PROXY_PORT = 9000
"""
    Default port for Scoop Proxy for a given process.
    Will be incremented by 1 for each new parallel process.
"""

#
# Scoop settings
#
SCOOP_CLI_OPTIONS = {
    "--log-level": "info",
    # "--signing-url": """,
    # "--signing-token": "",
    "--screenshot": "true",
    "--pdf-snapshot": "false",
    "--dom-snapshot": "false",
    "--capture-video-as-attachment": "true",
    "--capture-certificates-as-attachment": "true",
    "--provenance-summary": "true",
    "--attachments-bypass-limits": "true",
    "--capture-timeout": 50 * 1000,
    "--load-timeout": 25 * 1000,
    "--network-idle-timeout": 25 * 1000,
    "--behaviors-timeout": 15 * 1000,
    "--capture-video-as-attachment-timeout": 20 * 1000,
    "--capture-certificates-as-attachment-timeout": 10 * 1000,
    "--capture-window-x": 1600,
    "--capture-window-y": 900,
    "--max-capture-size": int(200 * 1024 * 1024),
    "--auto-scroll": "true",
    "--auto-play-media": "true",
    "--grab-secondary-resources": "true",
    "--run-site-specific-behaviors": "true",
    "--headless": "false",  # Note: `xvfb-run --auto-servernum --` prefix may be needed if false.
    # "--user-agent-suffix": "",
    "--blocklist": "/https?:\/\/localhost/,0.0.0.0/8,10.0.0.0/8,100.64.0.0/10,127.0.0.0/8,169.254.0.0/16,172.16.0.0/12,192.0.0.0/29,192.0.2.0/24,192.88.99.0/24,192.168.0.0/16,198.18.0.0/15,198.51.100.0/24,203.0.113.0/24,224.0.0.0/4,240.0.0.0/4,255.255.255.255/32,::/128,::1/128,::ffff:0:0/96,100::/64,64:ff9b::/96,2001::/32,2001:10::/28,2001:db8::/32,2002::/16,fc00::/7,fe80::/10,ff00::/8",  # noqa
    "--public-ip-resolver-endpoint": "https://icanhazip.com",
}
"""
    Options passed to the Scoop CLI during capture.
    See https://github.com/harvard-lil/scoop for details.

    Options which cannot be set at config level are listed here:
    - utils.config_check.EXCLUDED_SCOOP_CLI_OPTIONS
"""

SCOOP_TIMEOUT_FUSE = 45
""" Number of seconds to wait before "killing" a Scoop progress after capture timeout. """
