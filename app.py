# coding=utf-8
from gevent import monkey
monkey.patch_all()
import falcon
import redis
from resources import Start, End, Answer
from db import create_engine
from models import metadata
from configuration import config

# ### 初始化redis客户端
redis_config = config['REDIS']
# 当decode_responses参数为True时redis-py会自动将redis返回的字符菜转换为unicode。
# 默认不这么做的原因是：如果需要转换结果为数字，先转换为unicode就造成了额外花销。
# 节点本身不会从redis读取大量数字，但在归档数据时可能需要注意。
redis_config.update(decode_responses=True)
r = redis.StrictRedis(**redis_config)

# ###初始化数据库
db = create_engine(config['DATABASE_URL'])
# 程序在创建表格之前会检测是否存在
metadata.create_all(db)

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
api.req_options.auto_parse_form_urlencoded = True

api.add_route('/api/start/{game_id}', Start(r))
api.add_route('/api/end/{game_id}', End(r))
api.add_route('/api/answer/{game_id}/{question_id}', Answer(db))

if __name__ == '__main__':
    from wsgiref import simple_server
    httpd = simple_server.make_server('127.0.0.1', 8000, api)
    httpd.serve_forever()