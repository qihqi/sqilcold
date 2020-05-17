import dataclasses
import unittest
from typing import Optional

from sqlalchemy import Integer, Column, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from sqilcold.dbapi import SerializableDB, DBA, sqldataclass
from sqilcold.serialization import fieldcopy


class DBApiTest(unittest.TestCase):

    def test_fieldcopy(self):

        class obj(object):
            pass

        data = {
            'field1': 'value1',
            'field2': 'value2',
            'field3': 'value3',
        }
        fields = ['field1', 'field2', 'field3']

        dest = {}
        fieldcopy(data, dest, fields)
        self.assertEqual(data, dest)

        dest2 = obj()
        fieldcopy(data, dest2, fields)
        self.assertEqual(data, dest2.__dict__)

        dest3 = {}
        fieldcopy(dest2, dest3, fields)
        self.assertEqual(data, dest3)

        dest4 = obj()
        fieldcopy(dest2, dest4, fields)
        self.assertEqual(data, dest4.__dict__)

    def test_dbmix(self):
        Base = declarative_base()
        class TestModel(Base):
            __tablename__ = 'test'
            key = Column(Integer, primary_key=True)
            value = Column(Integer)

        @dataclasses.dataclass
        class Wrapped(SerializableDB[TestModel]):
            db_class = TestModel
            key: Optional[int] = None
            value: Optional[int] = None

        x = Wrapped(1, 2)

        y = x.db_instance()
        self.assertEqual(type(y), TestModel)
        self.assertEqual(1, y.key)
        self.assertEqual(2, x.value)

        from_db = Wrapped.from_db_instance(y)
        self.assertEqual(x, from_db)

        serialized = x._to_dict()
        self.assertEqual({'key': 1, 'value': 2}, serialized)

        des = Wrapped.from_dict(serialized)
        self.assertEqual(x, des)

    def test_dbapi(self):
        Base = declarative_base()
        class TestModel(Base):
            __tablename__ = 'test'
            key = Column(Integer, primary_key=True, autoincrement=True)
            value = Column(Integer)

        @dataclasses.dataclass
        class Wrapped(SerializableDB[TestModel]):
            db_class = TestModel
            key: Optional[int] = None
            value: Optional[int] = None

        engine = create_engine('sqlite:///:memory:', echo=False)
        sessionfactory = sessionmaker(bind=engine)
        Base.metadata.create_all(engine)
        session = sessionfactory()
        dbapi = DBA(session)
        w = Wrapped(value=3)
        pkey = dbapi.create(w)
        session.commit()

        gotten = dbapi.get(Wrapped, pkey)

        self.assertEqual(w, gotten)

        w.value = 456
        dbapi.update_full(w)
        session.commit()

        self.assertEqual(dbapi.get(Wrapped, pkey).value, 456)

        self.assertEqual(dbapi.delete(w), 1)
        session.commit()

    def test_decorator(self):

        Base = declarative_base()

        @sqldataclass
        class TestModel(Base):
            __tablename__ = 'test'
            key = Column(Integer, primary_key=True, autoincrement=True)
            value = Column(Integer)

        engine = create_engine('sqlite:///:memory:', echo=False)
        sessionfactory = sessionmaker(bind=engine)
        Base.metadata.create_all(engine)
        session = sessionfactory()
        dbapi = DBA(session)
        w = TestModel(value=3)
        pkey = dbapi.create(w)
        session.commit()

        gotten = dbapi.get(TestModel, pkey)

        self.assertEqual(w, gotten)

        w.value = 456
        dbapi.update_full(w)
        session.commit()

        self.assertEqual(dbapi.get(TestModel, pkey).value, 456)

        self.assertEqual(dbapi.delete(w), 1)
        session.commit()


if __name__ == '__main__':
    unittest.main()

