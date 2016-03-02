# coding=utf-8
from urllib import urlencode

import falcon
import falcon.testing as testing
from fakeredis import FakeStrictRedis
import simplejson as json
from resources import Start
from hooks import extract_running_info


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
        querystring = urlencode({'uid': _uid, 'userinfo': 'nothing', 'hash': '1234'})
        body = self.simulate_request('/start/1', method='POST', query_string=querystring, decode='utf-8')
        self.assertEquals(falcon.HTTP_200, self.srmock.status)
        data = json.loads(body)
        self.assertIn('run_id', data, 'run_id has been set')
        self.assertIn('uid', data, 'uid has been set')
        self.assertEquals(_uid, data['uid'], 'use the old uid')
        self.assertEquals(str(data['uid']), self.redis.hget('game:1:run', data['run_id']),
                          'store run_id and uid in redis')
        self.assertIsNone(self.redis.hget('game:1:userinfo', data['uid']), 'should not save userinfo')

    def test_with_userinfo_only(self):
        querystring = urlencode({'userinfo': json.dumps({'a': '1', 'b': '2'})})
        body = self.simulate_request('/start/1', method='POST', query_string=querystring, decode='utf-8')
        self.assertEquals(falcon.HTTP_400, self.srmock.status)
        data = json.loads(body)
        self.assertEquals('Missing parameter', data['title'])

    def test_with_userinfo_and_hash(self):
        _hash = 105
        _userinfo = json.dumps({'field1': u'王思聪', 'field2': '15888888888'})
        querystring = urlencode({'userinfo': _userinfo, 'hash': _hash})
        body = self.simulate_request('/start/1', method='POST', query_string=querystring, decode='utf-8')
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
        querystring = urlencode({'userinfo': _userinfo, 'hash': _hash})
        self.redis.hset('game:1:userinfo', _hash, 'something different')
        body = self.simulate_request('/start/1', method='POST', query_string=querystring, decode='utf-8')
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
        querystring = urlencode({'userinfo': _userinfo, 'hash': _hash})
        self.redis.hset('game:1:userinfo', _hash, _userinfo)
        body = self.simulate_request('/start/1', method='POST', query_string=querystring, decode='utf-8')
        self.assertEquals(falcon.HTTP_200, self.srmock.status)
        data = json.loads(body)
        self.assertIn('run_id', data, 'run_id has been set')
        self.assertIn('uid', data, 'uid has been set')
        self.assertEquals(_hash, data['uid'], 'use the original hash as uid')
        self.assertEquals(str(data['uid']), self.redis.hget('game:1:run', data['run_id']),
                          'store run_id and uid in redis')
        self.assertEquals(_userinfo, self.redis.hget('game:1:userinfo', data['uid']), 'store userinfo and uid in redis')


class TestExtractRunningInfoHooks(testing.TestBase):
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
