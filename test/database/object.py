"""Object table"""

from mysqldb_wrapper import Base, Id
from test.database.child import Child


class Object(Base):
    """Object class"""

    __tablename__ = "object"

    def __init__(self, session=None, *args, **kwargs):
        super().__init__(session, *args, **kwargs)
        self._childs = None

    id = Id()
    hashed = bytes()
    number = int(1)
    string = str("string")
    boolean = bool(True)
    created_at = int()
    updated_at = int()

    def func(self):
        pass

    @classmethod
    def class_method(cls):
        pass

    @staticmethod
    def static_method(cls):
        pass

    @property
    def childs(self):
        if self._childs is None:
            self._childs = self._session.query(Child).where(Child.parent_id == self.id).all()
        return self._childs
