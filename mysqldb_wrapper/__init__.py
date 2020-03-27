"""MySQLdb wrapper for easy usage and encryption"""

import logging
import warnings

import MySQLdb
from MySQLdb.cursors import Cursor as MySQLCursor

import crypt
from .crypt import Id

warnings.filterwarnings("ignore", category=MySQLdb.Warning)


class Empty:
    pass


def diff(other):
    return {k: v for k, v in vars(other).items() if k not in vars(Empty).keys() and not callable(other.__dict__[k])}


def getattribute(cls, name):
    if name.startswith("_"):
        return object.__getattribute__(cls, name)
    return BaseOperator(name)


class BaseMetaclass(type):
    """BaseMetaclass"""

    def __new__(cls, clsname, superclasses, attributedict):
        cls.__getattribute__ = lambda a, b: getattribute(a, b)
        return type.__new__(cls, clsname, superclasses, attributedict)


class Base(metaclass=BaseMetaclass):
    """Base class for all databases"""

    def __init__(self, *args, **kwargs):
        dic = diff(type(self))
        for key, value in dic.items():
            setattr(self, key, value)
        for arg in args:
            for key, value in arg.items():
                if key in dic:
                    setattr(self, key, value)
        for key, value in kwargs.items():
            if key in dic:
                setattr(self, key, value)


class BaseOperator:
    """For operator operations"""

    def __init__(self, name):
        self.__name = name

    def __eq__(self, value):
        return (self.__name, value)


class Cursor:
    """Wrapper of the database cursor"""

    def __init__(self, cursor, logger):
        self.cursor = cursor
        self.logger = logger

    def __getattr__(self, name):
        return getattr(self.cursor, name)

    def execute(self, query, args=None):
        self.logger.info(query)
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
        except MySQLdb.OperationalError:
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
        except MySQLdb.OperationalError:
            self.reconnect()
            cursor = self.db.cursor(cursorclass)
        return Cursor(cursor, self.logger)

    def commit(self):
        try:
            self.db.commit()
        except MySQLdb.OperationalError:
            self.reconnect()
            self.db.commit()


class Session:
    """Creates and handles the database session"""

    def __init__(self, user, password, db_name, encryption_key, logging_handler=None):
        self.db = Database(user, password, db_name, encryption_key, logging_handler)
        for subclass in Base.__subclasses__():
            self.create_table(subclass)

    def close(self):
        self.db.close()

    def create_table(self, obj):
        query = "CREATE TABLE IF NOT EXISTS " + obj.__tablename__ + " ("
        has_id = False
        for key, value in vars(obj).items():
            if key.startswith("_"):
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
        cursor.execute(query)

    def query(self, obj):
        return Query(self.db, obj)

    def add(self, obj):
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

    def __init__(self, db, obj):
        self.db = db
        self.obj = obj
        self.query = "SELECT * FROM " + obj.__tablename__
        self.all_values = []
        self.where_is_used = False

    def first(self):
        self.query += ";"
        cursor = self.db.cursor(MySQLdb.cursors.DictCursor)
        if self.all_values:
            cursor.execute(self.query, self.all_values)
        else:
            cursor.execute(self.query)
        result = cursor.fetchone()
        self.query = self.query[:-1]
        if not result:
            return None
        return crypt.decrypt_obj(self.obj(result))

    def all(self):
        self.query += ";"
        cursor = self.db.cursor(MySQLdb.cursors.DictCursor)
        if self.all_values:
            cursor.execute(self.query, self.all_values)
        else:
            cursor.execute(self.query)
        results = list(cursor.fetchall())
        self.query = self.query[:-1]
        if not results:
            return None
        to_return = []
        for result in results:
            to_return.append(crypt.decrypt_obj(self.obj(result)))
        return to_return

    def delete(self):
        to_delete = self.all()
        for o in to_delete:
            delete(self.db, o)

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


def delete(db, obj):
    dic = vars(obj)
    if "id" not in dic:
        return
    query = "DELETE FROM " + obj.__tablename__ + " WHERE id = " + str(dic["id"]) + ";"
    cursor = db.cursor()
    cursor.execute(query)
    db.commit()
    obj.id = Id()
