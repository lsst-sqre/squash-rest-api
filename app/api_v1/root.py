from flask import url_for
from flask_restful import Resource


class Root(Resource):

    def external_url(self, endpoint):
        return url_for(endpoint, _external=True)

    def get(self):

        # List of URLs we want in the API root, one can add more
        # but remember that removing may impact the clients

        response = {'job_url': self.external_url('job'),
                    'metrics_url': self.external_url('metrics'),
                    'apidocs_url': self.external_url('flasgger.apidocs'),
                    'users': self.external_url('users'),
                    'register_url': self.external_url('register'),
                    'version_url': self.external_url('version')}

        return response
