# coding=utf-8
import falcon
import redis
from resources import Start


"""
### API接口

按falcon的设计模式，每条url规则对应一个[资源]

* /api/start/{game_id}  - [开始游戏]
* /api/end/{game_id}
* /api/answer/{game_id}/{question_id}

[资源]: resources.html
[开始游戏]: resources.html#Start
"""
r = redis.StrictRedis()

api = falcon.API()
api.add_route('/api/start/{game_id}', Start(r))