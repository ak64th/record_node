# coding=utf-8
import uuid
import datetime

import simplejson as json
import falcon
import hooks

from models import records


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

        返回

        - run_id -- 分配的run_id
        - uid -- 分配的uid，需要填写字段时才会返回
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
        p = self.redis.pipeline()
        p.hset('game:%s:run' % game_id, run_id, uid)
        p.hset('game:%s:start' % game_id, run_id,  datetime.datetime.utcnow())
        p.execute()
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
            elif saved == userinfo:
                uid = _hash
            _hash += 1
        return uid


@falcon.before(hooks.extract_running_info)
class End(object):
    """
    ###<a name="End">结束游戏</a>
    将用户的uid，run_id和最终成绩保存到redis上，并更新该用户的最佳成绩
    """
    def __init__(self, redis):
        self.redis = redis

    def on_post(self, req, resp, game_id, uid, run_id):
        """客户端结束游戏时请求这个接口
        利用redis的sorted list维护成绩榜单,并为每个用户记录最佳成绩和最佳排名

        可能的请求参数有

        - score -- 用户得分

        返回

        - rank -- 本次得分的排名
        - best_score -- 曾经取得的最好得分，uid不为None时才会返回
        - best_rank -- 曾经取得的最好名次，uid不为None时才会返回
        """
        score = req.get_param_as_int('score', required=True)

        p = self.redis.pipeline()
        # redis的sorted set在分值相同时按照key的字母顺序排列
        # 为了能够得到并列的排名，维护一个key和score都是得分的sorted set
        p.zadd('game:%s:scores' % game_id, score, score)
        # 获取该分数的当前排名
        p.zrevrank('game:%s:scores' % game_id, score)

        # 如果uid不为None，需要更新用户最佳成绩
        if uid:
            p.hget('game:%s:record:scores' % game_id, uid)
            p.hget('game:%s:record:ranks' % game_id, uid)

        p.hset('game:%s:final' % game_id, run_id, score)
        p.hset('game:%s:end' % game_id, run_id,  datetime.datetime.utcnow())

        result = p.execute()
        data = {'rank': result[1]}

        if uid:
            # convert to int if not None
            best_score, best_rank = map(lambda i: int(i) if i else i, result[2:4])
            # update best score and rank
            if best_score is None or score > best_score:
                best_score = score
                p.hset('game:%s:record:scores' % game_id, uid, best_score)
            if best_rank is None or data['rank'] < best_rank:
                best_rank = data['rank']
                p.hset('game:%s:record:ranks' % game_id, uid, best_rank)
            data.update({'best_score': best_score, 'best_rank': best_rank})
            p.execute()

        resp.body = json.dumps(data)


@falcon.before(hooks.extract_running_info)
class Answer(object):
    """
    ###<a name="Answer">记录答题选择</a>
    保存用户答题过程
    """
    def __init__(self, db):
        self.db = db

    def on_post(self, req, resp, game_id, question_id, uid, run_id):
        """客户端在用户每次答题时将选择发送到这个借口
        客户端不应该等待这个接口回复

        可能的请求参数有

        - selected -- 用户选择的选项id号，多个选项用逗号连接，字符串
        - correct -- 是否正确，会被转化为bool类型。空白或不发送表示错误，也可以用'true'和'false'明确指定

        返回

        - inserted -- 一个数组，包含了插入记录的id
        """
        selected = req.get_param('selected')
        if not selected:
            correct = False
        else:
            correct = req.get_param_as_bool('correct') or False
        sql = records.insert().values(
            uid=uid,
            run=run_id,
            game=game_id,
            question=question_id,
            selected=selected,
            correct=correct,
        )
        with self.db.connect() as connection:
            result = connection.execute(sql)
        resp.body = json.dumps({'inserted': result.inserted_primary_key})
