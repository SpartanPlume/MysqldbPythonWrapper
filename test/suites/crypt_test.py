"""All tests concerning encryption and decryption of the data"""

import unittest
import copy

import crypt


class Test:
    def __init__(self):
        self.number = 1
        self.boolean = True
        self.string = "test"


class CryptTestCase(unittest.TestCase):
    def test_hash(self):
        """Test hashing a string"""
        initial_string = "test"
        new_string = crypt.hash_value(initial_string)
        self.assertNotEqual(initial_string, new_string)

    def test_crypt_obj(self):
        """Test encrypting an object and decrypting it"""
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
