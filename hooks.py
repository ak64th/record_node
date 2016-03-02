# coding=utf-8
def extract_running_info(req, resp, resource, params):
    """提取请求中的run_id和uid参数
    run_id是必填项，uid为空时表示本次活动不记录用户信息
    """
    params['run_id'] = req.get_param('run_id', required=True).lower()
    params['uid'] = req.get_param_as_int('uid')