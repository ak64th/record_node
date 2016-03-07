import gevent
from gevent import monkey
monkey.patch_all()
import os
import timeit
import sqlalchemy
import sqlalchemy.event
import sqlalchemy.pool
from sqlalchemy import Table, Column, Integer, String, MetaData

try:
    from pysqlite2 import dbapi2
except ImportError:
    from sqlite3 import dbapi2
print(dbapi2.sqlite_version_info)

if os.path.exists('tt.db'):
    os.remove('tt.db')


def set_sqlite_pragma(dbapi_connection, connection_record):
    dbapi_connection.isolation_level = None
    cursor = dbapi_connection.cursor()
    cursor.execute('PRAGMA journal_mode = WAL')
    print cursor.fetchone()
    cursor.execute('PRAGMA synchronous = NORMAL')
    dbapi_connection.commit()


metadata = MetaData()

records = Table(
    'records', metadata,
    Column('id', Integer, primary_key=True),
    Column('code', String)
)

engine = sqlalchemy.create_engine('sqlite:///tt.db', module=dbapi2, poolclass=sqlalchemy.pool.StaticPool)
sqlalchemy.event.listen(engine, 'connect', set_sqlite_pragma)

metadata.create_all(engine)


def block_test(times=100, run_foo=False):
    def ins(n):
        with engine.connect() as conn:
            conn.execute(records.insert().values(code=n))

    def foo():
        for j in range(5):
            print(j)
            gevent.sleep(0.1)

    greens = [gevent.spawn(ins, i) for i in range(times)]
    if run_foo:
        greens.append(gevent.spawn(foo))
    gevent.joinall(greens)


print(timeit.Timer(stmt='block_test(times=1000)', setup='from __main__ import block_test').timeit(number=1))
print(engine.execute(records.count()).fetchone())
print(timeit.Timer(stmt='block_test(times=1000, run_foo=True)', setup='from __main__ import block_test').timeit(number=1))
print(engine.execute(records.count()).fetchone())
