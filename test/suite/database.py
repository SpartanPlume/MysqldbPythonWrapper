"""All tests concerning the mysqldb_wrapper"""

import unittest
from cryptography.fernet import Fernet

from mysqldb_wrapper import Session
from test.database.test import Test
from config import constants


class DatabaseTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.session = Session(
            constants.DB_USERNAME,
            constants.DB_PASSWORD,
            constants.DB_TEST,
            Fernet.generate_key(),
        )

    @classmethod
    def tearDownClass(cls):
        cls.session.close()

    def test_add_object(self):
        """Add an object to the database"""
        obj = Test(hashed="abcd", number=1, string="a", boolean=True)
        self.session.add(obj)
        self.assertGreater(obj.id, 0)

    def test_query_first_object(self):
        """Query an object from the database"""
        obj = self.session.query(Test).first()
        self.assertIsNotNone(obj)
        self.assertNotEqual(obj.hashed, "abcd")
        self.assertEqual(obj.number, 1)
        self.assertEqual(obj.string, "a")
        self.assertEqual(obj.boolean, True)

    def test_delete_object(self):
        """Delete an object of the database"""
        obj = Test(hashed="abcd", number=2, string="a", boolean=False)
        self.session.add(obj)  # Already tested
        self.session.delete(obj)
        self.assertEqual(obj.id, 0)

    def test_update_object(self):
        """Update an object in the database"""
        obj = self.session.query(Test).first()  # Already tested
        obj.number = 2553166
        obj.string = "word"
        obj.boolean = True
        self.session.update(obj)
        obj = self.session.query(Test).first()  # Already tested
        self.assertEqual(obj.number, 2553166)
        self.assertEqual(obj.string, "word")
        self.assertEqual(obj.boolean, True)

    def test_query_where_object_by_id(self):
        """Query an object by id from the database"""
        obj = Test(hashed="efgh", number=1, string="word", boolean=True)
        self.session.add(obj)
        new_obj = self.session.query(Test).where(Test.id == obj.id).first()
        self.assertIsNotNone(obj)
        self.assertEqual(obj.id, new_obj.id)
        self.assertNotEqual(obj.hashed, "abcd")

    def test_query_where_object_by_hash(self):
        """Query an object by a hashed field from the database"""
        obj = self.session.query(Test).where(Test.hashed == "efgh").first()
        self.assertIsNotNone(obj)
        self.assertEqual(obj.number, 1)
        self.assertNotEqual(obj.hashed, "efgh")

    def test_query_where_object_by_crypted_value(self):
        """Query an object by a crypted field from the database"""
        obj = self.session.query(Test).where(Test.number == 1).first()
        self.assertIsNotNone(obj)
        self.assertEqual(obj.number, 1)

    def test_query_all_object(self):
        """Query all objects from the database"""
        list_obj = self.session.query(Test).all()
        self.assertIsNotNone(list_obj)
        self.assertEqual(len(list_obj), 2)

    def test_query_chaining_where(self):
        """Query all objects from the database"""
        obj = Test(hashed="aaaa", number=1, string="word", boolean=True)
        self.session.add(obj)
        obj = Test(hashed="aaaa", number=2, string="word", boolean=True)
        self.session.add(obj)
        list_obj = (
            self.session.query(Test)
            .where(Test.hashed == "aaaa")
            .where(Test.id == obj.id)
            .all()
        )
        self.assertIsNotNone(list_obj)
        self.assertEqual(len(list_obj), 1)

    def test_query_delete_object(self):
        """Delete all objects from the database by query"""
        query = self.session.query(Test)
        list_obj = query.all()
        self.assertIsNotNone(list_obj)
        query.delete()
        list_obj = query.all()
        self.assertIsNone(list_obj)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(DatabaseTestCase("test_add_object"))
    suite.addTest(DatabaseTestCase("test_query_first_object"))
    suite.addTest(DatabaseTestCase("test_delete_object"))
    suite.addTest(DatabaseTestCase("test_update_object"))
    suite.addTest(DatabaseTestCase("test_query_where_object_by_id"))
    suite.addTest(DatabaseTestCase("test_query_where_object_by_hash"))
    suite.addTest(DatabaseTestCase("test_query_all_object"))
    suite.addTest(DatabaseTestCase("test_query_chaining_where"))
    suite.addTest(DatabaseTestCase("test_query_delete_object"))
    return suite
