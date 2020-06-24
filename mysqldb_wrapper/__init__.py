"""MySQLdb wrapper for easy usage and encryption"""

import copy
import datetime
import logging
import warnings

import MySQLdb
from MySQLdb.cursors import Cursor as MySQLCursor

import crypt
from .crypt import Id

warnings.filterwarnings("ignore", category=MySQLdb.Warning)

MYSQL_SERVER_IS_GONE = 2006
MYSQL_TABLE_ALREADY_EXISTS = 1050


class Empty:
    pass


def diff(other):
    return {k: v for k, v in vars(other).items() if k not in vars(Empty).keys() and not callable(other.__dict__[k])}


def getattribute(cls, name):
    if name.startswith("_") or isinstance(object.__getattribute__(cls, name), property):
        return object.__getattribute__(cls, name)
    return BaseOperator(name)


class BaseMetaclass(type):
    """BaseMetaclass"""

    def __new__(cls, clsname, superclasses, attributedict):
        cls.__getattribute__ = lambda a, b: getattribute(a, b)
        return type.__new__(cls, clsname, superclasses, attributedict)


class Base(metaclass=BaseMetaclass):
    """Base class for all databases"""

    def __init__(self, session=None, *args, **kwargs):
        dic = diff(type(self))
        for key, value in dic.items():
            if isinstance(getattr(type(self), key, None), property):
                continue
            setattr(self, key, value)
        for arg in args:
            for key, value in arg.items():
                if key in dic:
                    setattr(self, key, value)
        for key, value in kwargs.items():
            if key in dic:
                setattr(self, key, value)
        self._session = session

    def __deepcopy__(self, memo):
        new_obj = self.__class__(self._session)
        for key, value in vars(self).items():
            if not key.startswith("_"):
                setattr(new_obj, key, copy.deepcopy(value, memo))
        return new_obj


class BaseOperator:
    """For operator operations"""

    def __init__(self, name):
        self.__name = name

    def __eq__(self, value):
        return (self.__name, value)


class Cursor:
    """Wrapper of the database cursor"""

    def __init__(self, cursor, db):
        self.cursor = cursor
        self.db = db
        self.logger = db.logger

    def __getattr__(self, name):
        return getattr(self.cursor, name)

    def execute(self, query, args=None):
        self.logger.info(query)
        try:
            self.cursor.execute(query, args)
        except MySQLdb.OperationalError as e:
            error_code, _ = e.args
            if error_code != MYSQL_SERVER_IS_GONE:
                raise e
            self.db.reconnect()
            self.cursor.execute(query, args)


class Database:
    """Contains the connection to the database and other informations"""

    def __init__(self, user, password, db_name, encryption_key, logging_handler=None):
        crypt.init(encryption_key)
        self.user = user
        self.password = password
        self.db_name = db_name
        self.logger = logging.getLogger("mysql")
        self.logger.setLevel(logging.DEBUG)
        if logging_handler:
            self.logger.addHandler(logging_handler)
        self.logger.info("Connecting to the database " + db_name + "...")
        try:
            self.db = MySQLdb.connect(user=user, passwd=password, db=db_name)
        except MySQLdb.OperationalError as e:
            error_code, _ = e.args
            if error_code != MYSQL_SERVER_IS_GONE:
                raise e
            self.db = MySQLdb.connect(user=user, passwd=password)
            query = "CREATE DATABASE " + db_name + ";"
            cursor = self.cursor()
            cursor.execute(query)
            self.db.commit()
            self.db.close()
            self.db = MySQLdb.connect(user=user, passwd=password, db=db_name)
        self.logger.info("Connection to the database " + db_name + " established.")

    def close(self):
        self.db.close()

    def reconnect(self):
        self.logger.info("Reconnecting to the database " + self.db_name + "...")
        self.db = MySQLdb.connect(user=self.user, passwd=self.password, db=self.db_name)
        self.logger.info("Reconnection to the database " + self.db_name + "successful.")

    def cursor(self, cursorclass=MySQLCursor):
        try:
            cursor = self.db.cursor(cursorclass)
        except MySQLdb.OperationalError as e:
            error_code, _ = e.args
            if error_code != MYSQL_SERVER_IS_GONE:
                raise e
            self.reconnect()
            cursor = self.db.cursor(cursorclass)
        return Cursor(cursor, self)

    def commit(self):
        try:
            self.db.commit()
        except MySQLdb.OperationalError as e:
            error_code, _ = e.args
            if error_code != MYSQL_SERVER_IS_GONE:
                raise e
            self.reconnect()
            self.db.commit()


class Session:
    """Creates and handles the database session"""

    def __init__(self, user, password, db_name, encryption_key, logging_handler=None):
        self.db = Database(user, password, db_name, encryption_key, logging_handler)
        self._init_tables(Base.__subclasses__())

    def _init_tables(self, tables):
        for table in tables:
            if subtables := table.__subclasses__():
                self._init_tables(subtables)
            elif getattr(table, "__tablename__"):
                self.create_table(table)

    def close(self):
        self.db.close()

    def create_table(self, obj):
        query = "CREATE TABLE " + obj.__tablename__ + " ("
        has_id = False
        for key, value in vars(obj).items():
            if key.startswith("_") or isinstance(value, property) or callable(value):
                continue
            if key == "id":
                has_id = True
                query += key + " MEDIUMINT NOT NULL AUTO_INCREMENT, "
            elif isinstance(getattr(obj(), key), crypt.Id):
                query += key + " MEDIUMINT, "
            else:
                query += key + " BLOB, "
        if has_id:
            query += "PRIMARY KEY (id), "
        if query.endswith("("):
            query = query[:-2]
        else:
            query = query[:-2]
            query += ")"
        query += ";"
        cursor = self.db.cursor()
        try:
            cursor.execute(query)
        except MySQLdb.OperationalError as e:
            error_code, _ = e.args
            if error_code != MYSQL_TABLE_ALREADY_EXISTS:
                raise e
            self.update_table(obj)

    def update_table(self, obj):
        query = "DESC " + obj.__tablename__ + ";"
        cursor = self.db.cursor()
        cursor.execute(query)
        current_columns = set([column[0] for column in cursor.fetchall()])
        obj_columns = set()
        for key, value in vars(obj).items():
            if key.startswith("_") or isinstance(value, property) or callable(value):
                continue
            obj_columns.add(key)
        columns_to_add = obj_columns - current_columns
        columns_to_delete = current_columns - obj_columns
        for column_to_add in columns_to_add:
            query = "ALTER TABLE " + obj.__tablename__ + " ADD COLUMN " + column_to_add
            value = None
            if isinstance(getattr(obj(), column_to_add), crypt.Id):
                query += " MEDIUMINT DEFAULT %s"
                value = [0]
            else:
                query += " BLOB DEFAULT %s"
                value = [crypt.encrypt_value(obj.__dict__[column_to_add])]
            query += ";"
            cursor = self.db.cursor()
            cursor.execute(query, value)
            self.db.commit()
        for column_to_delete in columns_to_delete:
            query = "ALTER TABLE " + obj.__tablename__ + " DROP COLUMN " + column_to_delete + ";"
            cursor = self.db.cursor()
            cursor.execute(query)
            self.db.commit()

    def query(self, obj):
        return Query(self, obj)

    def add(self, obj):
        obj._session = self
        if "created_at" in obj.__dict__:
            obj.created_at = int(datetime.datetime.utcnow().timestamp())
        if "updated_at" in obj.__dict__:
            obj.updated_at = int(datetime.datetime.utcnow().timestamp())
        encrypted_obj = crypt.encrypt_obj(obj)
        query = "INSERT INTO " + obj.__tablename__ + " ("
        all_values = []
        for key, value in vars(encrypted_obj).items():
            if key.startswith("_") or key == "id":
                continue
            query += key + ","
            all_values.append(value)
        if query.endswith("("):
            return obj
        query = query[:-1]
        query += ") VALUES ("
        for _ in range(len(all_values)):
            query += "%s,"
        query = query[:-1]
        query += ");"
        cursor = self.db.cursor()
        cursor.execute(query, all_values)
        self.db.commit()
        obj.id = cursor.lastrowid
        return obj

    def update(self, obj):
        if "updated_at" in obj.__dict__:
            obj.updated_at = int(datetime.datetime.utcnow().timestamp())
        encrypted_obj = crypt.encrypt_obj(obj)
        query = "UPDATE " + obj.__tablename__ + " SET "
        all_values = []
        obj_id = -1
        for key, value in vars(encrypted_obj).items():
            if key == "id":
                obj_id = value
                continue
            if key.startswith("_"):
                continue
            query += key + " = %s, "
            all_values.append(value)
        if obj_id < 0:
            return None
        query = query[:-2]
        query += " WHERE id = " + str(obj_id) + ";"
        cursor = self.db.cursor()
        cursor.execute(query, all_values)
        self.db.commit()
        return obj

    def delete(self, obj):
        return delete(self.db, obj)


class Query:
    """A class that is returned when asking to do a query"""

    def __init__(self, session, obj):
        self.session = session
        self.obj = obj
        self.query = "SELECT * FROM " + obj.__tablename__
        self.all_values = []
        self.where_is_used = False

    def first(self):
        self.query += ";"
        cursor = self.session.db.cursor(MySQLdb.cursors.DictCursor)
        if self.all_values:
            cursor.execute(self.query, self.all_values)
        else:
            cursor.execute(self.query)
        result = cursor.fetchone()
        self.query = self.query[:-1]
        if not result:
            return None
        return crypt.decrypt_obj(self.obj(self.session, result))

    def all(self):
        self.query += ";"
        cursor = self.session.db.cursor(MySQLdb.cursors.DictCursor)
        if self.all_values:
            cursor.execute(self.query, self.all_values)
        else:
            cursor.execute(self.query)
        results = list(cursor.fetchall())
        self.query = self.query[:-1]
        if not results:
            return []
        to_return = []
        for result in results:
            to_return.append(crypt.decrypt_obj(self.obj(self.session, result)))
        return to_return

    def delete(self):
        to_delete = self.all()
        delete(self.session.db, to_delete)

    def where(self, *args):
        for key, value in args:
            if self.where_is_used:
                self.query += " AND "
            else:
                self.where_is_used = True
                self.query += " WHERE "
            self.query += key + " = %s"
            if isinstance(getattr(self.obj(), key), bytes):
                self.all_values.append(crypt.hash_value(value))
            else:
                self.all_values.append(value)
        return self


def delete(db, to_delete):
    if not to_delete:
        return
    if not isinstance(to_delete, list):
        to_delete = [to_delete]
    for obj in to_delete:
        dic = vars(obj)
        if "id" not in dic:
            return
        query = "DELETE FROM " + obj.__tablename__ + " WHERE id = " + str(dic["id"]) + ";"
        cursor = db.cursor()
        cursor.execute(query)
        db.commit()
        obj.id = Id()
