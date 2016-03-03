# coding=utf-8
import falcon
import redis
from resources import Start, End, Answer
from db import create_engine
from models import metadata

# ### 初始化redis客户端
# 当decode_responses参数为True时redis-py会自动将redis返回的字符菜转换为unicode。
# 默认不这么做的原因是：如果需要转换结果为数字，先转换为unicode就造成了额外花销。
# 节点本身不会从redis读取大量数字，但在归档数据时可能需要注意。
r = redis.StrictRedis(decode_responses=True)

# ###初始化数据库
db = create_engine('sqlite:///records.db')
# 程序在创建表格之前会检测是否存在
metadata.create_all(metadata)

"""
### API接口

按falcon的设计模式，每条url规则对应一个[资源]

* /api/start/{game_id} - [开始游戏]
* /api/end/{game_id} - [结束游戏]
* /api/answer/{game_id}/{question_id} - [记录答题选择]

[资源]: resources.html
[开始游戏]: resources.html#Start
[结束游戏]: resources.html#End
[记录答题选择]: resources.html#Answer
"""
api = falcon.API()
api.add_route('/api/start/{game_id}', Start(r))
api.add_route('/api/end/{game_id}', End(r))
api.add_route('/api/answer/{game_id}/{question_id}', Answer(db))