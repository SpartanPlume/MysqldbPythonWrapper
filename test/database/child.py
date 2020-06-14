"""Child test table"""

from mysqldb_wrapper import Base, Id
from test.database.parent import Parent


class Child(Parent):
    """Child test class"""

    __tablename__ = "child"

    id = Id()
    parent_id = Id()
