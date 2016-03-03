# coding=utf-8
# 优先使用pysqlite2，python自带的sqlite3和pysqlite2是一个代码库，但版本较低
try:
    from pysqlite2 import dbapi2
except ImportError:
    from sqlite3 import dbapi2

import sqlalchemy
from sqlalchemy import event


def set_sqlite_pragma(dbapi_connection, connection_record):
    """为sqlite连接设置[PRAGMA语句](https://www.sqlite.org/pragma.html)
    sqlite的PRAGMA语句需要在每次连接开始时执行
    """
    cursor = dbapi_connection.cursor()
    # 设置sqlite到[WAL模式](https://www.sqlite.org/wal.html)
    # 需要sqlite3.7.0版本以上支持
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


def create_engine(url, **kwargs):
    engine = sqlalchemy.create_engine(url, module=dbapi2, **kwargs)
    # 只在sqlite3.7以上版本时开启WAL模式
    if dbapi2.sqlite_version_info[1] >= 7:
        event.listen(engine, 'connect', set_sqlite_pragma)
    return engine

