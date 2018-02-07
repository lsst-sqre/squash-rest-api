from flask import url_for
from flask_restful import Resource


class Root(Resource):
    """ List of urls we want in the API root."""

    def external_url(self, endpoint):
        return url_for(endpoint, _external=True)

    def get(self):
        response = {'job': self.external_url('job'),
                    'metrics': self.external_url('metrics'),
                    'apidocs': self.external_url('flasgger.apidocs'),
                    'users': self.external_url('users'),
                    'register': self.external_url('register'),
                    'version': self.external_url('version'),
                    'auth': self.external_url('_default_auth_request_handler'),
                    'monitor': self.external_url('monitor')}

        return response
