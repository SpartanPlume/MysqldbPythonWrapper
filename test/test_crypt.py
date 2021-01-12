"""All tests concerning the encryption and decryption of the data"""

import copy

from test.resources.mock import Matcher
from mysqldb_wrapper import crypt
from cryptography.fernet import Fernet
from test.database.object import Object


def test_hash():
    """Hash a string"""
    initial_string = "test"
    new_string = crypt.hash_value(initial_string)
    assert initial_string != new_string


def test_crypt_obj():
    """Encrypt an object and decrypt it"""
    obj = Object()
    crypt.init(Fernet.generate_key())
    new_obj = crypt.encrypt_obj(copy.deepcopy(obj))
    assert obj != Matcher(new_obj)
    new_obj = crypt.decrypt_obj(new_obj)
    assert obj == Matcher(new_obj)
