import falcon
import falcon.testing as testing
from fakeredis import FakeStrictRedis
import simplejson as json

from resources import Start


class TestStart(testing.TestBase):
    def before(self):
        resource = Start(FakeStrictRedis())
        self.api.add_route('/start/{game_id}', resource)

    def test_without_userinfo(self):
        body = self.simulate_request('/start/1', decode='utf-8', method='POST')
        self.assertEqual(self.srmock.status, falcon.HTTP_200)
        self.assertIs(True, 'run_id' in json.loads(body))
