"""Encrypt and decrypt datas"""

import copy
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
    return not isinstance(getattr(type(obj)(), key), bytes) and not isinstance(getattr(type(obj)(), key), Id)


def to_bytes(value):
    """Returns value as bytes"""
    if isinstance(value, str):
        return bytes(value, "utf-8")
    if isinstance(value, bool) or isinstance(value, int):
        number = int(value)
        return number.to_bytes((number.bit_length() + 7) // 8, "big", signed=False)
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


def encrypt_value(value):
    """Encrypts a value"""
    return _fernet.encrypt(to_bytes(value))


def encrypt_obj(obj):
    """Encrypts an object"""
    if not obj:
        return None
    encrypted_obj = copy.deepcopy(obj)
    fields = vars(encrypted_obj)
    for key, value in fields.items():
        if key.startswith("_") or isinstance(value, (property, classmethod, staticmethod)) or callable(value):
            continue
        if is_encrypted(encrypted_obj, key):
            setattr(encrypted_obj, key, _fernet.encrypt(to_bytes(value)))
        elif isinstance(getattr(type(encrypted_obj)(), key), bytes) and not isinstance(value, bytes):
            setattr(encrypted_obj, key, hash_value(value))
    return encrypted_obj


def decrypt_obj(obj):
    """Decrypts an object"""
    if not obj:
        return None
    decrypted_obj = copy.deepcopy(obj)
    fields = vars(decrypted_obj)
    for key, value in fields.items():
        if key.startswith("_") or isinstance(value, (property, classmethod, staticmethod)) or callable(value):
            continue
        if is_encrypted(decrypted_obj, key) and value:
            setattr(decrypted_obj, key, from_bytes(_fernet.decrypt(value), getattr(type(decrypted_obj)(), key)))
        elif not value:
            setattr(decrypted_obj, key, getattr(type(decrypted_obj)(), key))
    return decrypted_obj
