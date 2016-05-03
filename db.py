# coding=utf-8
# 优先使用pysqlite2，python自带的sqlite3和pysqlite2是一个代码库，但版本较低
try:
    from pysqlite2 import dbapi2
except ImportError:  # pragma: no cover
    from sqlite3 import dbapi2

import sqlalchemy
from sqlalchemy import event, pool


def set_sqlite_pragma(dbapi_connection, connection_record):
    """为sqlite连接设置[PRAGMA语句](https://www.sqlite.org/pragma.html)
    sqlite的PRAGMA语句需要在每次连接开始时执行
    """
    # 切换sqlite3到autocommit模式
    dbapi_connection.isolation_level = None
    cursor = dbapi_connection.cursor()
    # 设置sqlite到[WAL模式](https://www.sqlite.org/wal.html)
    # 需要sqlite3.7.0版本以上支持
    cursor.execute('PRAGMA journal_mode = WAL')
    # sqlite3文档中说WAL模式下默认同步模式是NORMAL，但实际上还是需要手动设置
    cursor.execute('PRAGMA synchronous = NORMAL')
    dbapi_connection.commit()


def create_engine(url, **kwargs):
    """
    ###创建数据库
    参照benchmark.py的结果，sqlite3查询会阻塞整个进程。解决办法是尽量快速完成写入。
    在部署产品时务必确保sqlite3版本高于3.7.0,否则低下的写入性能会影响网站响应
    """
    # 只会有写入操作，写入时整个文件加锁，无法并发写入。所以用StaticPool，确保所有greenlet只使用一个连接，除去反复建立连接的开销。
    # 如果需要读取数据库，可以换成QueuePool或SingletonThreadPool
    engine = sqlalchemy.create_engine(url, module=dbapi2, poolclass=sqlalchemy.pool.StaticPool, **kwargs)
    # 只在sqlite3.7以上版本时开启WAL模式
    if dbapi2.sqlite_version_info >= (3, 7, 0):
        event.listen(engine, 'connect', set_sqlite_pragma)
    return engine
