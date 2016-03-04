# coding=utf-8
from urllib import urlencode

import falcon
import falcon.testing as testing
from fakeredis import FakeStrictRedis
import simplejson as json
import sqlalchemy.event

from models import records, metadata
# ###测试以下的模块
from resources import Start, End, Answer
from hooks import extract_running_info
from db import create_engine, set_sqlite_pragma, dbapi2


# noinspection PyArgumentList
class TestStart(testing.TestBase):
    # noinspection PyAttributeOutsideInit
    def before(self):
        self.redis = FakeStrictRedis()
        self.resource = Start(self.redis)
        self.api.add_route('/start/{game_id}', self.resource)

    def after(self):
        self.redis.flushall()
        del self.redis

    def test_without_userinfo(self):
        body = self.simulate_request('/start/1', decode='utf-8', method='POST')
        self.assertEquals(falcon.HTTP_200, self.srmock.status)
        data = json.loads(body)
        self.assertIn('run_id', data, 'run_id has been set')
        self.assertIsNone(self.redis.hget('game:1:run', data['run_id']), 'redis hash should be empty')

    def test_with_uid(self):
        _uid = 25
        query_string = urlencode({'uid': _uid, 'userinfo': 'nothing', 'hash': '1234'})
        body = self.simulate_request('/start/1', method='POST', query_string=query_string, decode='utf-8')
        self.assertEquals(falcon.HTTP_200, self.srmock.status)
        data = json.loads(body)
        self.assertIn('run_id', data, 'run_id has been set')
        self.assertIn('uid', data, 'uid has been set')
        self.assertEquals(_uid, data['uid'], 'use the old uid')
        self.assertEquals(str(data['uid']), self.redis.hget('game:1:run', data['run_id']),
                          'store run_id and uid in redis')
        self.assertIsNone(self.redis.hget('game:1:userinfo', data['uid']), 'should not save userinfo')

    def test_with_userinfo_only(self):
        query_string = urlencode({'userinfo': json.dumps({'a': '1', 'b': '2'})})
        body = self.simulate_request('/start/1', method='POST', query_string=query_string, decode='utf-8')
        self.assertEquals(falcon.HTTP_400, self.srmock.status)
        data = json.loads(body)
        self.assertEquals('Missing parameter', data['title'])

    def test_with_userinfo_and_hash(self):
        _hash = 105
        _userinfo = json.dumps({'field1': u'王思聪', 'field2': '15888888888'})
        query_string = urlencode({'userinfo': _userinfo, 'hash': _hash})
        body = self.simulate_request('/start/1', method='POST', query_string=query_string, decode='utf-8')
        self.assertEquals(falcon.HTTP_200, self.srmock.status)
        data = json.loads(body)
        self.assertIn('run_id', data, 'run_id has been set')
        self.assertIn('uid', data, 'uid has been set')
        self.assertEquals(_hash, data['uid'], 'use the old uid')
        self.assertEquals(str(data['uid']), self.redis.hget('game:1:run', data['run_id']),
                          'store run_id and uid in redis')
        self.assertEquals(_userinfo, self.redis.hget('game:1:userinfo', data['uid']), 'store userinfo and uid in redis')

    def test_with_userinfo_and_hash_collision(self):
        _hash = 105
        _userinfo = json.dumps({'field1': u'王思聪', 'field2': '15888888888'})
        query_string = urlencode({'userinfo': _userinfo, 'hash': _hash})
        self.redis.hset('game:1:userinfo', _hash, 'something different')
        body = self.simulate_request('/start/1', method='POST', query_string=query_string, decode='utf-8')
        self.assertEquals(falcon.HTTP_200, self.srmock.status)
        data = json.loads(body)
        self.assertIn('run_id', data, 'run_id has been set')
        self.assertIn('uid', data, 'uid has been set')
        self.assertNotEquals(_hash, data['uid'], 'generate a new uid different from original hash')
        self.assertEquals(str(data['uid']), self.redis.hget('game:1:run', data['run_id']),
                          'store run_id and uid in redis')
        self.assertEquals(_userinfo, self.redis.hget('game:1:userinfo', data['uid']), 'store userinfo and uid in redis')

    def test_with_used_userinfo_and_hash(self):
        _hash = 105
        _userinfo = json.dumps({'field1': u'王思聪', 'field2': '15888888888'})
        query_string = urlencode({'userinfo': _userinfo, 'hash': _hash})
        self.redis.hset('game:1:userinfo', _hash, _userinfo)
        body = self.simulate_request('/start/1', method='POST', query_string=query_string, decode='utf-8')
        self.assertEquals(falcon.HTTP_200, self.srmock.status)
        data = json.loads(body)
        self.assertIn('run_id', data, 'run_id has been set')
        self.assertIn('uid', data, 'uid has been set')
        self.assertEquals(_hash, data['uid'], 'use the original hash as uid')
        self.assertEquals(str(data['uid']), self.redis.hget('game:1:run', data['run_id']),
                          'store run_id and uid in redis')
        self.assertEquals(_userinfo, self.redis.hget('game:1:userinfo', data['uid']), 'store userinfo and uid in redis')


# noinspection PyArgumentList
class TestEnd(testing.TestBase):
    # noinspection PyAttributeOutsideInit
    def before(self):
        self.redis = FakeStrictRedis()
        self.redis.zadd('game:1:scores', 100, 100)
        self.redis.zadd('game:1:scores', 110, 110)
        self.resource = End(self.redis)
        self.api.add_route('/end/{game_id}', self.resource)

    def after(self):
        self.redis.flushall()
        del self.redis

    def test_without_uid(self):
        _run_id = 'some_random_thing'
        _score = 105
        query_string = urlencode({'run_id': _run_id, 'score': _score})
        body = self.simulate_request('/end/1', method='POST', query_string=query_string, decode='utf-8')
        self.assertEquals(falcon.HTTP_200, self.srmock.status)
        data = json.loads(body)
        self.assertIn('rank', data, 'rank has been set')
        self.assertNotIn('best_score', data, 'no best_score')
        self.assertNotIn('best_rank', data, 'no best_rank')
        self.assertEquals(1, data['rank'], 'rank should be 1')
        self.assertEquals(str(_score), self.redis.hget('game:1:final', _run_id))

    def test_with_uid(self):
        _run_id = 'some_random_thing'
        _score = 105
        _uid = 15
        query_string = urlencode({'run_id': _run_id, 'score': _score, 'uid': _uid})
        body = self.simulate_request('/end/1', method='POST', query_string=query_string, decode='utf-8')
        self.assertEquals(falcon.HTTP_200, self.srmock.status)
        data = json.loads(body)
        self.assertIn('rank', data, 'rank has been set')
        self.assertIn('best_score', data, 'best_score has been set')
        self.assertIn('best_rank', data, 'best_rank has been set')
        self.assertEquals(1, data['rank'], 'rank should be 1')
        self.assertEquals(_score, data['best_score'], 'score should be set as best score')
        self.assertEquals(1, data['best_rank'], 'best_rank should be 1')
        self.assertEquals(str(_score), self.redis.hget('game:1:final', _run_id))

    def test_update_best_records(self):
        _run_id = 'some_random_thing'
        _score = 105
        _uid = 15
        query_string = urlencode({'run_id': _run_id, 'score': _score, 'uid': _uid})
        self.redis.hset('game:1:record:scores', _uid, 100)
        self.redis.hset('game:1:record:ranks', _uid, 2)
        body = self.simulate_request('/end/1', method='POST', query_string=query_string, decode='utf-8')
        self.assertEquals(falcon.HTTP_200, self.srmock.status)
        data = json.loads(body)
        self.assertIn('rank', data, 'rank has been set')
        self.assertIn('best_score', data, 'best_score has been set')
        self.assertIn('best_rank', data, 'best_rank has been set')
        self.assertEquals(1, data['rank'], 'rank should be 1')
        self.assertEquals(_score, data['best_score'], 'score should be set as best score')
        self.assertEquals(1, data['best_rank'], 'best_rank should be 1')
        self.assertEquals(str(_score), self.redis.hget('game:1:final', _run_id))

    def test_oot_update(self):
        _run_id = 'some_random_thing'
        _score = 105
        _uid = 15
        query_string = urlencode({'run_id': _run_id, 'score': _score, 'uid': _uid})
        self.redis.hset('game:1:record:scores', _uid, 150)
        self.redis.hset('game:1:record:ranks', _uid, 0)
        body = self.simulate_request('/end/1', method='POST', query_string=query_string, decode='utf-8')
        self.assertEquals(falcon.HTTP_200, self.srmock.status)
        data = json.loads(body)
        self.assertIn('rank', data, 'rank has been set')
        self.assertIn('best_score', data, 'best_score has been set')
        self.assertIn('best_rank', data, 'best_rank has been set')
        self.assertEquals(1, data['rank'], 'rank should be 1')
        self.assertEquals(150, data['best_score'], 'score should be 150')
        self.assertEquals(0, data['best_rank'], 'best_rank should be 0')
        self.assertEquals(str(_score), self.redis.hget('game:1:final', _run_id))


# noinspection PyArgumentList
class TestAnswer(testing.TestBase):
    # noinspection PyAttributeOutsideInit
    def before(self):
        self.db = create_engine('sqlite://')
        metadata.create_all(self.db)
        self.resource = Answer(self.db)
        self.api.add_route('/answer/{game_id}/{question_id}', self.resource)

        # test data
        self.test_run_id = self.getUniqueString('run_id')
        self.test_score = self.getUniqueInteger()
        self.test_uid = self.getUniqueInteger()
        self.test_selected = self.getUniqueInteger()

    def after(self):
        self.db.dispose()
        del self.db

    def test_with_correct_answer(self):
        query_string = urlencode({
            'run_id': self.test_run_id,
            'uid': self.test_uid,
            'selected': self.test_selected,
            'correct': 'true'
        })
        body = self.simulate_request('/answer/1/12 ', method='POST', query_string=query_string, decode='utf-8')
        self.assertEquals(falcon.HTTP_200, self.srmock.status)
        data = json.loads(body)
        self.assertIn('inserted', data, 'return inserted id')
        self.assertEquals([1], data['inserted'])
        row = self.db.execute(records.select()).fetchone()
        self.assertIn(row['id'], data['inserted'])
        self.assertEquals(1, row['game'])
        self.assertEquals(12, row['question'])
        self.assertEquals(self.test_run_id, row['run'])
        self.assertEquals(self.test_uid, row['uid'])
        self.assertEquals(self.test_selected, row['selected'])
        self.assertTrue(row['correct'])

    def test_with_no_correction(self):
        query_string = urlencode({
            'run_id': self.test_run_id,
            'uid': self.test_uid,
            'selected': self.test_selected,
        })
        body = self.simulate_request('/answer/1/12 ', method='POST', query_string=query_string, decode='utf-8')
        self.assertEquals(falcon.HTTP_200, self.srmock.status)
        data = json.loads(body)
        self.assertIn('inserted', data, 'return inserted id')
        self.assertEquals([1], data['inserted'])
        row = self.db.execute(records.select()).fetchone()
        self.assertIn(row['id'], data['inserted'])
        self.assertEquals(1, row['game'])
        self.assertEquals(12, row['question'])
        self.assertEquals(self.test_run_id, row['run'])
        self.assertEquals(self.test_uid, row['uid'])
        self.assertEquals(self.test_selected, row['selected'])
        self.assertFalse(row['correct'])

    def test_with_no_selected(self):
        query_string = urlencode({
            'run_id': self.test_run_id,
            'uid': self.test_uid,
            'correct': 'true'
        })
        body = self.simulate_request('/answer/1/12 ', method='POST', query_string=query_string, decode='utf-8')
        self.assertEquals(falcon.HTTP_400, self.srmock.status)
        data = json.loads(body)
        self.assertEquals('Missing parameter', data['title'])
        row = self.db.execute(records.select()).fetchone()
        self.assertIsNone(row, 'no data was inserted')


class TestExtractRunningInfoHook(testing.TestBase):
    # noinspection PyAttributeOutsideInit
    def before(self):
        validate_resource = falcon.before(extract_running_info)(testing.TestResource)
        self.resource = validate_resource()
        self.api.add_route(self.test_route, self.resource)

    def test_with_only_run_id(self):
        _run_id = 'some_random_thing'
        query_string = urlencode({'run_id': _run_id})
        self.simulate_request(self.test_route, query_string=query_string)
        self.assertEquals(falcon.HTTP_200, self.srmock.status)
        self.assertIn('run_id', self.resource.kwargs)
        self.assertIn('uid', self.resource.kwargs)
        self.assertEquals(_run_id, self.resource.kwargs['run_id'])
        self.assertIsNone(self.resource.kwargs['uid'])

    def test_with_run_id_and_uid(self):
        _uid = 105
        _run_id = 'some_random_thing'
        query_string = urlencode({'run_id': _run_id, 'uid': _uid})
        self.simulate_request(self.test_route, query_string=query_string)
        self.assertEquals(falcon.HTTP_200, self.srmock.status)
        self.assertIn('run_id', self.resource.kwargs)
        self.assertIn('uid', self.resource.kwargs)
        self.assertEquals(_run_id, self.resource.kwargs['run_id'])
        self.assertEquals(_uid, self.resource.kwargs['uid'])

    def test_without_run_id(self):
        _uid = 105
        query_string = urlencode({'uid': _uid})
        body = self.simulate_request(self.test_route, query_string=query_string, decode='utf-8')
        self.assertEquals(falcon.HTTP_400, self.srmock.status)
        data = json.loads(body)
        self.assertEquals('Missing parameter', data['title'])


class TestCreateDBEngine(testing.TestBase):
    def test_set_pragma(self):
        db = create_engine('sqlite://')
        db.connect()
        is_listening = sqlalchemy.event.contains(db, 'connect', set_sqlite_pragma)
        if dbapi2.sqlite_version_info > (3, 7, 0):
            self.assertTrue(is_listening)
        else:
            self.expectFailure("turn on pragma with sqlite version <= 3.7.0",
                               self.assertTrue, is_listening)