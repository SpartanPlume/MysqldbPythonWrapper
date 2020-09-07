"""All Tosurnament module mock objects."""

import json
import os
from unittest import mock

from mysqldb_wrapper import crypt


def query_side_effect_wrapper(session_mock):
    """Side effect for the query function, used to return the stubs in the storage."""

    def query_side_effect(table):
        tablename = table.__tablename__
        if tablename in session_mock.tables:
            query_mock = QueryMock(session_mock, session_mock.tables[tablename])
        else:
            query_mock = QueryMock(session_mock, [])
        return query_mock

    return query_side_effect


def add_side_effect_wrapper(session_mock):
    """Side effect for the add function, used to add an id to the input table."""

    def add_side_effect(table):
        tablename = table.__tablename__
        if tablename in session_mock.tables and len(session_mock.tables[tablename]) > 0:
            max_id = 0
            stub_id_present = False
            for stub in session_mock.tables[tablename]:
                if stub.id > max_id:
                    max_id = stub.id
                if stub.id == table.id:
                    stub_id_present = True
            if stub_id_present:
                table.id = max_id + 1
        else:
            session_mock.tables[tablename] = []
            if table.id < 1:
                table.id = 1
        session_mock.tables[tablename].append(table)
        return table

    return add_side_effect


def delete_side_effect_wrapper(session_mock):
    """Side effect for the add function, used to add an id to the input table."""

    def delete_side_effect(table):
        if table:
            tablename = table.__tablename__
            if tablename in session_mock.tables:
                stubs = session_mock.tables[tablename]
                for index, stub in enumerate(stubs):
                    if stub.id == table.id:
                        session_mock.tables[tablename].pop(index)
                        table.id = 0
                        return table
        return table

    return delete_side_effect


class QueryMock:
    def __init__(self, mock_session, stubs):
        self.mock_session = mock_session
        self.stubs = stubs

    def where(self, *args):
        for key, value in args:
            selected_stubs = []
            for stub in self.stubs:
                if getattr(stub, key) == value:
                    selected_stubs.append(stub)
            self.stubs = selected_stubs
        return self

    def first(self):
        if self.stubs:
            return self.stubs[0]
        return None

    def all(self):
        return self.stubs

    def delete(self):
        for stub in self.stubs:
            self.mock_session.delete(stub)


class SessionMock:
    """A mock for the session. Includes utility functions to simulate a storage."""

    def __init__(self):
        self.tables = {}
        self.add = mock.Mock(side_effect=add_side_effect_wrapper(self))
        self.update = mock.Mock(side_effect=(lambda x: x))
        self.query = mock.MagicMock(side_effect=query_side_effect_wrapper(self))
        self.delete = mock.MagicMock(side_effect=delete_side_effect_wrapper(self))

    def add_stub(self, stub):
        """Adds a stub in the mock. The added stubs will be used when retrieving an object."""
        stub._session = self
        add_side_effect_wrapper(self)(stub)

    def reset_stub(self, table):
        """Resets all the stubs of the table."""
        self.tables[table.__tablename__] = []


def compare_table_objects(self, other):
    """Compares 2 table class objects."""
    if not type(self) == type(other):
        return False
    fields = vars(self)
    for key in fields.keys():
        if (
            not key.startswith("_")
            and key not in ["created_at", "updated_at"]
            and (crypt.is_encrypted(self, key) or (isinstance(getattr(type(self)(), key), crypt.Id) and key != "id"))
        ):
            print(key, getattr(self, key), getattr(other, key))
            if getattr(self, key) != getattr(other, key):
                return False
    return True


class Matcher:
    """Comparator of table class objects. To use with mock.call and to check against a call_args_list."""

    def __init__(self, table_obj):
        self.table_obj = table_obj

    def __eq__(self, other):
        return compare_table_objects(self.table_obj, other)

    def __ne__(self, other):
        return not self.__eq__(other)
