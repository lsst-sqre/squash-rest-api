from flask import Flask
from flask_restful import Api
from flask_jwt import JWT

from flasgger import Swagger

from .auth import authenticate, identity
from .db import db
from .resources.user import User, UserList, Register
from .resources.metric import Metric, MetricList
from .resources.measurement import Measurement, MeasurementList


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

    # add api documentation
    Swagger(app)

    api.add_resource(User, '/user/<string:username>')
    api.add_resource(UserList, '/users')
    api.add_resource(Register, '/register')
    api.add_resource(Metric, '/metric/<string:name>')
    api.add_resource(MetricList, '/metrics')
    api.add_resource(Measurement, '/measurement/<string:job>')
    api.add_resource(MeasurementList, '/measurements')

    return app
