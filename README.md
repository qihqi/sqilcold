# sqilcold

sqilcold is a small wrapper to turn SqlAlchemy ORM classes into
dataclasses.

### Why?

* I am not a fan of Active Record pattern. I don't like DB record to modify 
  accidentally if I modify a field of an object.

* dataclass is easier to convert to dict / json.


# Example:

    Base = declarative_base()

    @sqilcold.sqldataclass
    class TestModel(Base):

        __tablename__ = 'test'
        key = Column(Integer, primary_key=True, autoincrement=True)
        value = Column(Integer)
        date = Column(DateTime)
        str_val = Column(String(20))

Now TestModel is a dataclass instead of a TestModel. We can still do database things to it.

    engine = create_engine('sqlite:///:memory:', echo=False)
    sessionfactory = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    session = sessionfactory()
    dba = sqilcold.DBA(session)

### create
    t = TestModel()
    t.value = 2
    t.date = datetime.datetime.now()
    t.str_val  = 'hello'
    pkey_val = dba.create(t)
    print(pkey_val)  # prints 1 as this is the primary key db assigned to it
    assert pkey_val == t.key  # primary key is also modified in the object

### load via primary key
    t = dba.get(TestModel, 1)
    assert isinstance(t, TestModel)
    # the values are what you saved
    assert t.value == 2

### modify
    t.value = 3
The line above does not modify the record in DB
only the value in the object.
To modify the record in db, run:

    dba.update_full(t)

    # You can also update some (but not all) fields instead
    dba.update(t, {'value': 4})  # this will change t.value to 4 and its corresponding db record

**NOTE:** `dba.update_full(t)` is equivalent to `dba.update(t, t.__dict__)`

**NOTE2:** the object passed to `dba.update` does not need to be loaded by `dba`;
You can do

    temp = TestModel()
    temp.key = 1
    dba.update(temp, {'value': 4})
    
the above will have the same effect on the database.

## Search
    dba.search(TestModel, {'value': 4})  # return an iterator of TestModel where value is 4

    # getone
    dba.getone(TestModel, dict(value=4)) # same api as search, but return first item instead of a iterator.

    ## Get access to underlying SQLAlchemy object

    print(session.query(TestModel.db_class).all())  # should see the record just created

## Serialilze
    print(t.to_json())
    
## deserialize

    TestModel.from_json(t.to_json()) == t
