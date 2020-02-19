"""Encrypt and decrypt datas"""

import hashlib

from cryptography.fernet import Fernet


_fernet = None


class Id(int):
    """Special class to not encrypt"""

    pass


def init(encryption_key):
    """Sets the encryption key for all later uses of crypt"""
    global _fernet
    _fernet = Fernet(encryption_key)


def is_encrypted(obj, key):
    """Checks if the database object field is encrypted or to be encrypted"""
    return not isinstance(getattr(type(obj)(), key), bytes) and not isinstance(
        getattr(type(obj)(), key), Id
    )


def to_bytes(value):
    """Returns value as bytes"""
    if isinstance(value, str):
        return bytes(value, "utf-8")
    if isinstance(value, bool) or isinstance(value, int):
        number = int(value)
        return number.to_bytes((number.bit_length() + 7) // 8, "big", signed=True)
    return value


def from_bytes(value, value_type):
    """Returns the value from bytes depending on the type"""
    if isinstance(value_type, str):
        return value.decode("utf-8")
    if isinstance(value_type, bool) or isinstance(value_type, int):
        number = int.from_bytes(value, "big", signed=True)
        if isinstance(value_type, bool):
            return bool(number)
        return number
    return value


def hash_value(value):
    """Hashes a string"""
    if not value:
        return None
    return hashlib.blake2b(to_bytes(value)).digest()


def encrypt_obj(obj):
    """Encrypts an object"""
    if not obj:
        return None
    fields = vars(obj)
    for key, value in fields.items():
        if not key.startswith("_"):
            if is_encrypted(obj, key):
                setattr(obj, key, _fernet.encrypt(to_bytes(value)))
            elif isinstance(getattr(type(obj)(), key), bytes) and not isinstance(
                value, bytes
            ):
                setattr(obj, key, hash_value(value))
    return obj


def decrypt_obj(obj):
    """Decrypts an object"""
    if not obj:
        return None
    fields = vars(obj)
    for key, value in fields.items():
        if not key.startswith("_") and is_encrypted(obj, key):
            setattr(
                obj, key, from_bytes(_fernet.decrypt(value), getattr(type(obj)(), key))
            )
    return obj
