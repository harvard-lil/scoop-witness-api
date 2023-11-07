"""
`models.access_key` module: Class to interact wit the "access_key" table.
"""
import uuid

import bcrypt
import peewee

from ..utils import get_db


class AccessKey(peewee.Model):
    """
    "access_key" table definition. Helps manage access to the API.
    """

    id_access_key = peewee.AutoField()

    created_timestamp = peewee.TimestampField(utc=True, resolution=1000, null=False)

    canceled_timestamp = peewee.TimestampField(utc=True, resolution=1000, null=True, default=None)

    label = peewee.TextField(null=False)

    key_digest = peewee.CharField(max_length=256, null=False, unique=True, index=True)
    """Argon2 digest."""

    class Meta:
        table_name = "access_key"
        database = get_db()

    @classmethod
    def create_key_digest(cls, key="", salt="") -> tuple:
        """
        Hashes a key using bcrypt.
        - Will automatically generate an access key if "key" is not provided (uuid4).
        - Returns a tuple containing the key and its digest
        """
        key = str(key)

        if not key:
            key = str(uuid.uuid4())

        if not salt:
            salt = bcrypt.gensalt()

        digest = bcrypt.hashpw(key.encode(), salt)
        return (key, digest)
