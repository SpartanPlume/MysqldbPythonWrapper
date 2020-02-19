"""Test table"""

from mysqldb_wrapper import Base, Id


class Test(Base):
    """Test class"""

    __tablename__ = "test"

    id = Id()
    hashed = bytes()
    number = int(1)
    string = str("string")
    boolean = bool(True)

    def func(self):
        pass
