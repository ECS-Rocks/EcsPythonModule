import json
import urllib3


class EcsApiInterface:

    def __init__(self, method_path: str):
        self._http = urllib3.PoolManager()
        self._endpoint_url = "https://api.ecs.rocks" + method_path


    def __call__(self, request_data: dict, verb: str = "POST", headers: dict = None):
        default_headers = { "Content-Type": "application/json" }
    
        result = self._http.request(
            verb,
            self._endpoint_url,
            body=json.dumps(request_data),
            headers=(default_headers if headers is None else headers)
        )
    
        return json.loads(result.data.decode("utf-8"))
