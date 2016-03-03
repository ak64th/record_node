# coding=utf-8
from datetime import datetime
from sqlalchemy import Table, Column, Integer, String, MetaData, DateTime

# ###数据库结构
metadata = MetaData()

# 记录用户答题记录
records = Table(
    'records', metadata,
    Column('id', Integer, primary_key=True),
    Column('uid', Integer),
    Column('run', String),
    Column('question', Integer),
    Column('selected', Integer),
    Column('timestamp', DateTime, default=datetime.utcnow),
)