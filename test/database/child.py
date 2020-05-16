"""Child test table"""

from mysqldb_wrapper import Base, Id


class Child(Base):
    """Child test class"""

    __tablename__ = "child"

    id = Id()
    parent_id = Id()
    number = int()
