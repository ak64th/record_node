# coding=utf-8
import uuid
import simplejson as json


class Start(object):
    """
    ###<a name="Start">开始游戏</a>
    为用户分配uid，为当前游戏分配run_id,，数据保存在redis上
    """
    def __init__(self, redis):
        self.redis = redis

    def on_post(self, req, resp, game_id):
        """客户端开始游戏时请求这个接口
        如果请求中不包含uid和userinfo，说明本次活动不需要填写字段，直接分配一个run_id。

        如果请求中包含uid，在回复信息中包含uid，否则用hash参数作为key检查redis上是否已经存在保存的字符串，生成uid

        可能的请求参数有

        - userinfo -- 用户填写的信息
        - uid -- 客户端保存的uid，是一个32位整数
        - hash -- 客户端根据用户信息生成的hash值，是一个32位整数
        """
        userinfo = req.get_param('userinfo', default=None)
        uid = req.get_param_as_int('uid')
        # 没有填写字段，直接生成run_id
        if not userinfo and not uid:
            resp.body = json.dumps({'run_id': self._new_run_id()})
            return
        if not uid:
            # 未分配uid时，客户端会根据用户填写字段用hash函数生成一个32位整数作为备选的uid
            _hash = req.get_param_as_int('hash', required=True)
            uid = self._set_uid(game_id, _hash, userinfo)
        run_id = self._new_run_id()
        self.redis.hset('game:%s:run' % game_id, run_id, uid)
        resp.body = json.dumps({'uid': uid, 'run_id': run_id})

    @staticmethod
    def _new_run_id():
        """生成一个新run_id"""
        return uuid.uuid4().hex

    def _set_uid(self, game_id, _hash, userinfo):
        """维护一个hash表保存为用户分配的uid和对应的用户信息

        也可以直接用userinfo作为uid，redis内部会进行hash。缺点是所有需要key的地方都要存这个字符串，占用空间大。hash函数反复执行，消耗性能。
        """
        uid = None
        while not uid:
            # 检查已经保存的数据防止hash冲突，大部分情况下第一次就会执行成功
            saved = self.redis.hget('game:%s:userinfo' % game_id, _hash)
            if not saved:
                uid = _hash
                self.redis.hset('game:%s:userinfo' % game_id, uid, userinfo)
            if saved == userinfo:
                uid = _hash
            _hash += 1
        return uid
