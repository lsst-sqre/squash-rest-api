from flask import Flask
from flask_restful import Api
from flask_jwt import JWT

from flasgger import Swagger

from .auth import authenticate, identity
from .db import db
from .resources.user import User, UserList, Register
from .resources.metric import Metric, MetricList
from .resources.specification import Specification, SpecificationList
from .resources.measurement import Measurement, MeasurementList
from .resources.job import Job, JobList


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

    template = {"tags": [{"name": "Metrics"},
                         {"name": "Metric Specifications"},
                         {"name": "Metric Measurements"},
                         {"name": "Jobs"},
                         {"name": "Users"}]}
    # Add api documentation
    Swagger(app, template=template)

    api.add_resource(Job, '/job/<string:ci_id>')
    api.add_resource(JobList, '/jobs')
    api.add_resource(User, '/user/<string:username>')
    api.add_resource(UserList, '/users')
    api.add_resource(Register, '/register')
    api.add_resource(Metric, '/metric/<string:name>')
    api.add_resource(MetricList, '/metrics')
    api.add_resource(Specification, '/specification/<string:name>')
    api.add_resource(SpecificationList, '/specifications')
    api.add_resource(Measurement, '/measurement/<string:ci_id>')
    api.add_resource(MeasurementList, '/measurements')

    return app
