from flask import Flask
from flask_restful import Api
from flask_jwt import JWT

from flasgger import Swagger

from .auth import authenticate, identity
from .db import db
from .resources.root import Root
from .resources.user import User, UserList, Register
from .resources.metric import Metric, MetricList
from .resources.specification import Specification, SpecificationList
from .resources.measurement import Measurement, MeasurementList
from .resources.job import Job, JobWithArg
from .resources.jenkins import Jenkins


def create_app(config):
    """Create an application instance."""

    app = Flask(__name__)
    app.config.from_object(config)

    # initialize extensions
    db.init_app(app)

    # add authentication route /auth
    JWT(app, authenticate, identity)

    # register api resources
    api = Api(app)

    template = {"tags": [{"name": "Jobs"},
                         {"name": "Metrics"},
                         {"name": "Metric Specifications"},
                         {"name": "Metric Measurements"},
                         {"name": "Users"}]}
    # Add api documentation
    Swagger(app, template=template)

    # Redirect root url to api documentation
    api.add_resource(Root, '/')

    # Generic Job resource
    api.add_resource(Job, '/job')

    # Because flasgger cannot handle endpoints with multiple URLs,
    # the methods that require the job_id argument are implemented
    # separately in a different resource.
    # See the status of this issue and the reason for this
    # workaround at
    # https://github.com/rochacbruno/flasgger/issues/174
    api.add_resource(JobWithArg, '/job/<int:job_id>')

    # Resource for jobs in the jenkins enviroment
    api.add_resource(Jenkins, '/jenkins/<string:ci_id>')

    # User resources
    api.add_resource(User, '/user/<string:username>')
    api.add_resource(UserList, '/users')
    api.add_resource(Register, '/register')

    # Metric resources
    api.add_resource(Metric, '/metric/<string:name>')
    api.add_resource(MetricList, '/metrics')

    # Metric specifications resources
    api.add_resource(Specification, '/spec/<string:name>')
    api.add_resource(SpecificationList, '/specs')

    # Metric measurement resources
    api.add_resource(Measurement, '/measurement/<int:job_id>')
    api.add_resource(MeasurementList, '/measurements')

    return app
