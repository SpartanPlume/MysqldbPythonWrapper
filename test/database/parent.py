"""Parent test table"""

from mysqldb_wrapper import Base, Id


class Parent(Base):
    """Parent test class"""

    def __init_subclass__(cls):
        super().__init_subclass__()
        cls.number = int()

    id = Id()
