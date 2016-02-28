# coding=utf-8
import simplejson as json


# noinspection PyMethodMayBeStatic
class Start(object):
    """<a name="Start">开始游戏</a>
    开始游戏时，网页端发送包含了用户信息的请求
    对于每个用户，按他填写的字段使用hash函数（比如md5）生成uid，如果不要求填写字段，则随机生成一个
    用户每次开始游戏，节点服务器把uid和对应字段（json形式）存放到redis的hash结构
    """
    def __init__(self, redis):
        self.redis = redis

    # noinspection PyUnusedLocal
    def on_post(self, req, resp, game_id):
        return json.dumps({'game_id': game_id})