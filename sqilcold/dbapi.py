import dataclasses
from collections import abc

from sqlalchemy.inspection import inspect

from typing import (Type, TypeVar, Generic,
                    Mapping, Optional, Any, Iterable)

from .serialization import fieldcopy
from .serialization import SerializableData


DBType = TypeVar('DBType')
SelfType = TypeVar('SelfType', bound='SerializableDB')
class SerializableDB(SerializableData, Generic[DBType]):
    """Interface for objects that knows how to convert into a db object.

    The db object can the be used with DBApiGeneric to save and store stuff.
    """

    # class of the db object
    db_class: Type[DBType]

    def db_instance(self) -> DBType:
        columns = inspect(self.db_class).columns
        result = self.db_class()
        fieldcopy(self, result, columns.keys())
        return result

    @classmethod
    def from_db_instance(cls: Type[SelfType], db_instance) -> SelfType:
        columns = inspect(cls.db_class).columns
        y = cls()
        fieldcopy(db_instance, y, columns.keys())
        return y


T = TypeVar('T', bound='SerializableDB')
class DBA(object):

    # db_class = database_class  # type: Type[DBType]
    # _columns = inspect(database_class).columns
    # pkey = inspect(database_class).primary_key[0]
    def __init__(self, session):
        self.session = session

    def create(self, obj: SerializableDB):
        """Insert a row into DB represented by obj.

        Args:
            obj: SerializableDB

        Returns:
            value of its primary key. This is useful if DB generates
            a primary key for you.
        """
        dbobj = obj.db_instance()
        self.session.add(dbobj)
        self.session.flush()
        pkey = self._get_pkey_name(type(obj))
        pkeyval = getattr(dbobj, pkey)
        setattr(obj, pkey, pkeyval)
        return pkeyval

    def get(self, objclass: Type[T], pkey) -> Optional[T]:
        """Get a row from DB given primary key.

        Args:
            objclass: the class type of object.
            pkey: primary key.

        Returns:
            None if no item if found.
            object of type objclass if found.
        """
        pkey_col = inspect(objclass.db_class).primary_key[0]
        db_instance = self.session.query(objclass.db_class).filter(
            pkey_col == pkey).first()
        if db_instance is None:
            return None
        return objclass.from_db_instance(db_instance)

    def update(self, obj: SerializableDB, content_dict: Mapping) -> int:
        pkey_col = inspect(obj.db_class).primary_key[0]
        pkey = getattr(obj, self._get_pkey_name(type(obj)))
        count = self.session.query(obj.db_class).filter(
            pkey_col == pkey).update(
            content_dict, synchronize_session='fetch')
        for x, y in list(content_dict.items()):
            setattr(obj, x, y)
        return count

    def update_full(self, obj: SerializableDB) -> int:
        columns = inspect(obj.db_class).columns
        pkey_col = inspect(obj.db_class).primary_key[0]
        pkey_name = self._get_pkey_name(type(obj))
        values = {col: getattr(obj, col)
                  for col in list(columns.keys())
                  if col != pkey_name}
        return self.update(obj, values)

    def delete(self, obj: SerializableDB) -> int:
        pkey_col = inspect(obj.db_class).primary_key[0]
        pkey = getattr(obj, self._get_pkey_name(type(obj)))
        count = self.session.query(obj.db_class).filter(
            pkey_col == pkey).delete(synchronize_session='fetch')
        return count

    def getone(self, objclass: Type[T], kwargs: Mapping[str, Any]) -> Optional[T]:
        try:
            result = self.search(objclass, kwargs)
            return next(iter(result))
        except:
            return None

    def search(
        self, objclass: Type[T], kwargs: Mapping[str, Any]) -> Iterable[T]:
        query = self.session.query(objclass.db_class)
        columns = inspect(objclass.db_class).columns
        for key, value in list(kwargs.items()):
            mode = None
            if '-' in key:
                key, mode = key.split('-')
            col = columns[key]
            f = col == value
            if mode == 'prefix':
                f = col.startswith(value)
            if mode == 'lte':
                f = col <= value
            if mode == 'gte':
                f = col >= value
            query = query.filter(f)
        return map(objclass.from_db_instance, iter(query))

    def _get_pkey_name(self, cls: Type[SerializableDB]) -> str:
        if hasattr(cls, '_pkey_name'):
            return getattr(cls, '_pkey_name')
        insp = inspect(cls.db_class)
        pkey_col = insp.primary_key[0]
        for key, val in insp.columns.items():
            if val.name == pkey_col.name:
                return key
        raise AssertionError('No primary key among columns', cls.__name__)


def sqldataclass(dbclass, override_name=None):
    columns_tuple = []
    columns = inspect(dbclass).columns
    classname = override_name or dbclass.__name__
    for c in columns:
        ptype = c.type.python_type
        if issubclass(ptype, abc.Iterable):
            field = dataclasses.field(default_factory=lambda: ptype())
        else:
            field = dataclasses.field(default=None)
        columns_tuple.append(
            (c.name, ptype, field))
    dc = dataclasses.make_dataclass(classname, columns_tuple, bases=(SerializableDB,))
    setattr(dc, 'db_class', dbclass)
    return dc

