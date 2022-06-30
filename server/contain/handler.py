import json, logging
logger = logging.getLogger(__name__)


class Handler:

    @staticmethod
    def parse_params(hdl):
        """
        解析请求数据
        支持：get、post、json
        """
        params = {}
        for key in hdl.request.arguments:
            params[key] = hdl.get_argument(key)

        # json
        content_type = hdl.request.headers.get('content-type', '')
        if hdl.request.is_post() and content_type.find('application/json') > -1:
            try:
                body = hdl.request.body.decode('utf-8')
                params = json.loads(body)
            except BaseException as e:
                logger.error("json请求数据解析异常")
                logger.error(e)

        hdl.params = hdl.request.params = params
        return params
