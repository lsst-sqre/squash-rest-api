from flask import url_for
from flask_restful import Resource


class Root(Resource):
    """ Lookup for resource URLs. """

    def external_url(self, endpoint):
        return url_for(endpoint, _external=True)

    def get(self):

        # List of resources we want in the API root
        endpoints = ['job', 'blob', 'metrics', 'specs', 'apidocs', 'users',
                     'register', 'version', 'auth', 'monitor', 'datasets',
                     'stats', 'packages', 'code_changes']

        root_url = url_for('root', _external=True)

        response = {key: root_url + key for key in endpoints}

        return response
