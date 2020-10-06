import json
import urllib3


class EcsApiInterface:
    """This class facilitates the use of our REST API by allowing us to call API endpoints like functions.

    ----

    To easily use one of the API endpoints of api.ecs.rocks, simply pass the endpoint's path to this class's
    ctor. For example, if you wanted to use parsePhoneNumber, you could simply construct an instance of this
    class as follows:
        parse_phone_number = ecs.EcsApiInterface(method_path="/v0/util/parsePhoneNumber")

    And then you could call it like so:
        parse_phone_number({
            "event-subject": "test",
            "event-body": "example"
        })

    ----

    For more details on the ECS REST API, visit https://api.ecs.rocks/docs or contact Dante@elkhornservice.com.

    """

    def __init__(self, method_path: str):
        self._http = urllib3.PoolManager()
        self._endpoint_url = "https://api.ecs.rocks" + method_path

    def __call__(self, request_data: dict, verb: str = "POST", headers: dict = None):
        """The function call operator is overloaded to call the API method passed to the ctor.

        :param request_data: the payload to send to the API (must be a JSON serializable dict)
        :param verb: the HTTP verb to use (defaults to POST)
        :param headers: request headers to be passed along with the payload (you probably don't need to use this)
        :return: response from the API
        """
        default_headers = {"Content-Type": "application/json"}

        result = self._http.request(
            verb,
            self._endpoint_url,
            body=json.dumps(request_data),
            headers=(default_headers if headers is None else headers)
        )

        return json.loads(result.data.decode("utf-8"))
