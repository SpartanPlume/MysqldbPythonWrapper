"""All tests concerning the mysqldb_wrapper"""

import time
import pytest
from cryptography.fernet import Fernet

from test.resources.mock import Matcher
from mysqldb_wrapper import Session, Base, Id
from test.database.object import Object
from test.database.child import Child
from test.database.parent import Parent
from config import constants

session = None


@pytest.fixture(scope="module")
def session():
    session = Session(constants.DB_USERNAME, constants.DB_PASSWORD, constants.DB_TEST, Fernet.generate_key())
    yield session
    session.close()


def test_add_object(session):
    """Add an object to the database"""
    obj = Object(hashed="abcd", number=1, string="a", boolean=True)
    session.add(obj)
    assert obj.id > 0


def test_query_first_object(session):
    """Query an object from the database"""
    obj = session.query(Object).first()
    assert obj == Matcher(Object(number=1, string="a", boolean=True))
    assert obj.hashed != "abcd"
    assert obj.created_at > 0
    assert obj.updated_at > 0


def test_delete_object(session):
    """Delete an object of the database"""
    obj = Object(hashed="abcd", number=2, string="a", boolean=False)
    session.add(obj)  # Already tested, id > 0
    session.delete(obj)
    assert obj.id == 0
    session.add(obj)
    obj.delete()
    assert obj.id == 0


def test_update_object(session):
    """Update an object in the database"""
    obj = session.query(Object).first()  # Already tested
    obj.update({"number": 1, "string": "word"}, number="2553166", boolean=True)
    session.update(obj)
    obj = session.query(Object).first()
    assert obj == Matcher(Object(string="word", number=2553166, boolean=True))


def test_query_where_object_by_id(session):
    """Query an object by id from the database"""
    obj = Object(hashed="efgh", number=1, string="word", boolean=True)
    session.add(obj)
    query_obj = session.query(Object).where(Object.id == obj.id).first()
    assert query_obj == Matcher(obj)
    query_obj = Object.get_from_id(session, obj.id)
    assert query_obj == Matcher(obj)


def test_query_where_object_by_hash(session):
    """Query an object by a hashed field from the database"""
    obj = Object(hashed="efgh", number=1, string="word", boolean=True)
    query_obj = session.query(Object).where(Object.hashed == "efgh").first()
    assert query_obj == Matcher(obj)
    assert query_obj.hashed != "efgh"


def test_query_all_object(session):
    """Query all objects from the database"""
    list_obj = session.query(Object).all()
    assert list_obj
    assert len(list_obj) == 2


def test_query_chaining_where(session):
    """Query all objects from the database"""
    obj = Object(hashed="aaaa", number=1, string="word", boolean=True)
    session.add(obj)
    obj2 = Object(hashed="aaaa", number=2, string="word", boolean=True)
    session.add(obj2)
    list_obj = session.query(Object).where(Object.hashed == "aaaa").where(Object.id == obj.id).all()
    assert list_obj == [Matcher(obj)]


def test_child_table(session):
    """Add a child and update, query, delete child via parent property"""
    obj = Object(hashed="aaaa", number=1, string="word", boolean=True)
    session.add(obj)
    child = Child(parent_id=obj.id, number=2)
    session.add(child)
    assert obj.childs == [Matcher(child)]
    obj.childs[0].number = 3
    session.update(obj.childs[0])
    child = session.query(Child).where(Child.parent_id == obj.id).first()
    assert child == Matcher(obj.childs[0])
    session.delete(obj.childs[0])
    child = session.query(Child).where(Child.parent_id == obj.id).first()
    assert not child


def test_query_delete_object(session):
    """Delete all objects from the database by query"""
    query = session.query(Object)
    list_obj = query.all()
    assert list_obj
    query.delete()
    list_obj = query.all()
    assert list_obj == []


def test_delete_none_or_empty(session):
    """Try to delete None or empty"""
    session.delete(None)
    session.delete([])


def test_parent_not_queryable(session):
    """Check that the Parent table is not queryable"""
    with pytest.raises(AttributeError):
        session.query(Parent).all()


def test_columns_addition_and_deletion(session):
    """Adds missing columns and delete unnecessary ones"""
    obj = Object(hashed="aaaa", number=1, string="word", boolean=True)
    session.add(obj)

    class Object2(Base):
        """New Object class"""

        __tablename__ = "object"

        id = Id()
        hashed = bytes()
        number = int(1)
        string = str("string")
        boolean = bool(True)
        new_column1 = Id()
        new_column2 = str("new_column")

    session._init_tables(Base.__subclasses__())
    obj = session.query(Object2).first()
    with pytest.raises(AttributeError):
        obj.created_at
    with pytest.raises(AttributeError):
        obj.update_at
    assert obj == Matcher(Object2(number=1, string="word", boolean=True, new_column1=0, new_column2="new_column"))
    session.query(Object2).delete()


def test_commit_timeout(session, mocker):
    """Tests commit timeout"""
    session.db.close = mocker.Mock()
    session.db.reconnect = mocker.Mock()
    session.db.db.commit = mocker.Mock(side_effect=(lambda: time.sleep(3)))
    obj = Child()
    session.add(obj)
    session.db.close.assert_called_once()
    session.db.reconnect.assert_called_once()
