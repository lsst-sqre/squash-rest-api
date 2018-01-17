from flask import url_for
from flask_restful import Resource


class Root(Resource):

    def external_url(self, endpoint):
        return url_for(endpoint, _external=True)

    def get(self):

        # List of URLs we want in the API root, one can add more
        # but remember that removing may impact the clients

        response = {'job': self.external_url('job'),
                    'metrics': self.external_url('metrics'),
                    'apidocs': self.external_url('flasgger.apidocs'),
                    'users': self.external_url('users'),
                    'register': self.external_url('register'),
                    'version': self.external_url('version'),
                    'auth': self.external_url('_default_auth_request_handler')}

        return response
