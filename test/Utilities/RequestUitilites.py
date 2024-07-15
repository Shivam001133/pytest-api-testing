import logging as logger
import json
import httpx
import httpx_cache
from simple_settings import settings
from test.src.constants import api_versions

class RequestsUtilities:

    def __init__(self):
        self.base_url = settings.API_HOST
        self.version = api_versions.NONE
        transport = httpx.AsyncHTTPTransport(retries=2)
        self.httpx_client = httpx.AsyncClient(transport=transport)
        self.client =  httpx_cache.AsyncClient(transport=transport)

    def get_url(self, endpoint, version=None):
        if version is None:
            version = self.version
        return f"{self.base_url}{version}{endpoint}"

    def get_headers(self, token=None):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Token {token}"
        return headers

    def assert_status_code(self, response, expected_status_code):
        if expected_status_code is not None:
            assert response.status_code == expected_status_code, (
                f'Bad Status code. Expected {expected_status_code}, '
                f'Actual status code: {response.status_code}, URL: {response.url}'
            )
    def mask_sensitive_info(self, data):
        sensitive_keys = ['authorization', 'Authorization']
        for key in sensitive_keys:
            if key in data:
                data[key] = '***masked***'
        return data

    def pretty_print_json(self, data):
        try:
            return json.dumps(data, indent=4, sort_keys=True)
        except (TypeError, json.JSONDecodeError):
            return data

    def log_api_details(self, response, request_data):

        log_message = [
            "--------- API Call Details ---------",
            f"URL: {response.request.url}",
            f"Method: {response.request.method}",
            "Request Headers: " + self.pretty_print_json(self.mask_sensitive_info(dict(response.request.headers))),
            "Request Body: " + self.pretty_print_json(self.mask_sensitive_info(request_data)),
            "Response Status: " + str(response.status_code),
            "Response Headers: " + self.pretty_print_json(self.mask_sensitive_info(dict(response.headers))),
        ]
        if response.headers.get('Content-Type', '').startswith('application/json'):
            log_message.append("Response Body (JSON): " + self.pretty_print_json(response.json()))
        else:
            log_message.append("Response Body: Response is not in JSON format. Printing response headers instead.")
            log_message.append(self.pretty_print_json(dict(response.headers)))

        logger.info("\n".join(log_message))

    def extract_response_body(self, response):
        if response.headers.get('Content-Type', '').startswith('application/json'):
            return response.json()
        return response.text

    async def _request(self, method, endpoint, version=None, payload=None, json=None, files=None, headers=None, params=None, expected_status_code:int=200, token:str=None, cache=None):
        url = self.get_url(endpoint, version)
        if not headers:
            headers = self.get_headers(token)

        if cache:
            response = await self.client.request(
                method,
                url,
                headers=headers,
                data=payload,
                json=json,
                files=files,
                params=params,
                timeout=None
                )
            logger.info("cache Stored")
        elif cache is None:
            raise ValueError("Cache parameter is not provided")
        else:
            response = await self.httpx_client.request(
                method,
                url,
                headers=headers,
                data=payload,
                json=json,
                files=files,
                params=params,
                timeout=None
                )
            logger.info("cache reused")

        self.log_api_details(
            response,
            dict(
                data=payload,
                json=json,
                files=files,
                params=params
                )
            )
        self.assert_status_code(response, expected_status_code)

        return self.extract_response_body(response)

    async def post(self, endpoint, version=None, payload=None, json=None, files=None, headers=None, params=None, expected_status_code:int=200, token:str=None, **kwargs):
        cache = kwargs.get('cache', None)
        return await self._request('POST', endpoint, version, payload, json, files, headers, params, expected_status_code, token, cache)

    async def get(self, endpoint, version=None, payload=None, headers=None, params=None, expected_status_code:int=200, token:str=None, **kwargs):
        cache = kwargs.get('cache', None)
        return await self._request('GET', endpoint, version, payload, None, None, headers, params, expected_status_code, token, cache)

    async def put(self, endpoint, payload=None, json=None, headers=None, params=None, expected_status_code:int=200, token:str=None,  **kwargs):
        cache = kwargs.get('cache', None)
        return await self._request('PUT', endpoint, None, payload, json, None, headers, params, expected_status_code, token, cache)

    async def patch(self, endpoint, payload=None, json=None, headers=None, params=None, expected_status_code:int=200, token:str=None, version=None,  **kwargs):
        cache = kwargs.get('cache', None)
        return await self._request('PATCH', endpoint, version, payload, json, None, headers, params, expected_status_code, token, cache)

    async def delete(self, endpoint, payload=None, version=None, json=None, headers=None, params=None, expected_status_code:int=200, token:str=None,  **kwargs):
        cache = kwargs.get('cache', None)
        return await self._request('DELETE', endpoint, version, payload, json, None, headers, params, expected_status_code, token, cache)
