"""Implement test client to test the SQuaSH API endpoints."""

import json
from urllib.parse import urlsplit, urlunsplit


class TestClient:
    """SQuaSH API test client.

    Parameters
    ----------
    app : `Flask app`
        SQuaSH API flask app.
    """

    def __init__(self, app):
        self.app = app
        self.auth = ""

    def set_auth(self, token):
        """Set authentication JWT token."""
        self.auth = "JWT " + token

    def send(
        self, url, method="GET", data=None, headers={}, json_response=True
    ):
        """Implement a generic request method."""
        # for testing, URLs just need to have the path and query string
        url_parsed = urlsplit(url)
        url = urlunsplit(
            ("", "", url_parsed.path, url_parsed.query, url_parsed.fragment)
        )

        # append the authentication headers to all requests
        headers = headers.copy()
        headers["Authorization"] = self.auth
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json"

        # convert JSON data to a string
        data = json.dumps(data)

        # send request to the test client and return the response
        with self.app.test_request_context(
            url, method=method, data=data, headers=headers
        ):
            rv = self.app.preprocess_request()
            if rv is None:
                rv = self.app.dispatch_request()
            rv = self.app.make_response(rv)
            rv = self.app.process_response(rv)

            if json_response:
                return rv, json.loads(rv.data.decode("utf-8"))
            else:
                return rv

    def get(self, url, headers={}, json_response=True):
        """GET request."""
        return self.send(
            url, "GET", headers=headers, json_response=json_response
        )

    def post(self, url, data={}, headers={}):
        """POST request."""
        return self.send(url, "POST", data, headers=headers)

    def put(self, url, data, headers={}):
        """PUT request."""
        return self.send(url, "PUT", data, headers=headers)

    def delete(self, url, headers={}):
        """DELETE request."""
        return self.send(url, "DELETE", headers=headers)
