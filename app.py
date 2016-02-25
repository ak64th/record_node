import falcon
import uuid
import simplejson as json


def check_or_set_uid(req, resp, resource, params):
    uid = req.cookies.get('uid')
    if not uid:
        uid = uuid.uuid4().hex[:8]
        resp.set_cookie("uid", uid, max_age=600, path='/rest', secure=False, http_only=False)
    params['uid'] = uid


@falcon.before(check_or_set_uid)
class Resource(object):
    def __init__(self, redis_client):
        self.redis = redis_client

    def on_post(self, req, resp, game_id, uid):
        return json.dumps({
            'message': 'Game %s for user %s started' % (game_id, uid),
        })


api = falcon.API()
api.add_route('/api/start_game/{game_id}', Resource())