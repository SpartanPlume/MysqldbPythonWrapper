"""All tests concerning the encryption and decryption of the data"""

import unittest
import copy

from mysqldb_wrapper import crypt
from cryptography.fernet import Fernet


class Test:
    def __init__(self):
        self.number = 1
        self.boolean = True
        self.string = "test"


class CryptTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        crypt.init(Fernet.generate_key())

    def test_hash(self):
        """Hash a string"""
        initial_string = "test"
        new_string = crypt.hash_value(initial_string)
        self.assertNotEqual(initial_string, new_string)

    def test_crypt_obj(self):
        """Encrypt an object and decrypt it"""
        obj = Test()
        new_obj = crypt.encrypt_obj(copy.deepcopy(obj))
        self.assertNotEqual(obj.number, new_obj.number)
        self.assertNotEqual(obj.boolean, new_obj.boolean)
        self.assertNotEqual(obj.string, new_obj.string)
        new_obj = crypt.decrypt_obj(new_obj)
        self.assertEqual(obj.number, new_obj.number)
        self.assertEqual(obj.boolean, new_obj.boolean)
        self.assertEqual(obj.string, new_obj.string)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(CryptTestCase("test_hash"))
    suite.addTest(CryptTestCase("test_crypt_obj"))
    return suite
