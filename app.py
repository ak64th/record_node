# coding=utf-8
import falcon
import redis
from resources import Start

# ### 初始化redis客户端
# 当decode_responses参数为True时redis-py会自动将redis返回的字符菜转换为unicode。
# 默认不这么做的原因是：如果需要转换结果为数字，先转换为unicode就造成了额外花销。
# 节点本身不会从redis读取大量数字，但在归档数据时可能需要注意。
r = redis.StrictRedis(decode_responses=True)

"""
### API接口

按falcon的设计模式，每条url规则对应一个[资源]

* /api/start/{game_id}  - [开始游戏]
* /api/end/{game_id}
* /api/answer/{game_id}/{question_id}

[资源]: resources.html
[开始游戏]: resources.html#Start
"""
api = falcon.API()
api.add_route('/api/start/{game_id}', Start(r))