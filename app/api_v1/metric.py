from flask_restful import Resource, reqparse
from flask_jwt import jwt_required

from sqlalchemy.orm import noload

from ..models import MetricModel


class Metric(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('description',
                        type=str,
                        required=True,
                        help="You must provide the package name associated "
                             "to this metric."
                        )
    parser.add_argument('package',
                        type=str
                        )
    parser.add_argument('unit',
                        type=str
                        )
    # accept multiple values
    # http://flask-restful.readthedocs.io/en/0.3.5/reqparse.html
    parser.add_argument('tags',
                        type=str, action="append"
                        )
    parser.add_argument('reference',
                        type=dict
                        )

    def get(self, name):
        """
        Retrieve a metric from its name.
        ---
        tags:
          - Metrics
        parameters:
        - name: name
          in: path
          type: string
          description: Full qualified name of the metric, e.g. validate_drp.AM1
          required: true
        responses:
          200:
            description: Metric found.
          404:
            description: Metric not found.
        """
        metric = MetricModel.find_by_name(name)

        if metric:
            return metric.json()

        return {'message': 'Metric not found'}, 404

    @jwt_required()
    def post(self, name):
        """
        Create a metric.
        ---
        tags:
          - Metrics
        parameters:
        - name: name
          in: path
          type: string
          description: Full qualified name of the metric, e.g. validate_drp.AM1
          required: true
        - in: body
          name: "Request body:"
          schema:
            type: object
            required:
              - description
            properties:
              description:
                type: string
              unit:
                type: string
              tags:
                type: array
              reference:
                type: object
        responses:
          201:
            description: Metric successfully created.
          400:
            description: A metric with this name already exists.
          401:
            description: >
                Authorization Required. Request does not contain a
                valid access token.
          500:
            description: An error occurred creating this metric.
        """

        data = Metric.parser.parse_args()

        if "." in name:
            data['package'], data['display_name'] = name.split(".")
        else:
            message = "You must provide a full qualified name for" \
                      " the metric, e.g. validate_drp.AM1"

            return {"message": message}

        # Metric names are unique
        if MetricModel.find_by_name(name):
            message = "A metric with name `{}` already exist.".format(name)
            return {'message': message}, 400

        metric = MetricModel(name, **data)

        try:
            metric.save_to_db()
        except:
            message = "An error ocurred creating metric `{}`.".format(name)
            return {"message": message}, 500

        return metric.json(), 201

    @jwt_required()
    def delete(self, name):
        """
        Delete a metric.
        ---
        tags:
          - Metrics
        parameters:
        - name: name
          in: path
          type: string
          description: Full qualified name of the metric, e.g. validate_drp.AM1
          required: true
        responses:
          200:
            description: Metric deleted.
          401:
            description: >
                Authorization Required. Request does not contain a
                valid access token.
          404:
            description: Metric not found.
        """

        metric = MetricModel.find_by_name(name)
        if not metric:
            return {"message": "Metric `{}` not found.".format(name)}, 404

        metric.delete_from_db()
        return {'message': 'Metric deleted.'}


class MetricList(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("metrics",
                        type=dict,
                        action="append"
                        )
    parser.add_argument('package')

    def get(self):
        """
        Retrieve the complete list of metrics.
        ---
        tags:
          - Metrics
        parameters:
          - name: package
            in: url
            type: string
            description: Name of the verification package to filter
        responses:
          200:
            description: List of metrics successfully retrieved.
        """

        queryset = MetricModel.query

        args = self.parser.parse_args()

        package = args['package']

        if package:
            queryset = queryset.filter(MetricModel.package == package)

        return {'metrics': [metric.json() for metric in
                            queryset.options(noload(MetricModel.measurement),
                            noload(MetricModel.specification)).all()]}

    @jwt_required()
    def post(self):
        """
        Create a list of metrics.
        ---
        tags:
          - Metrics
        parameters:
        - name: "Request body:"
          in: body
          schema:
            type: object
            required:
              - metrics
            properties:
              metrics:
                type: array
        responses:
          201:
            description: List of metrics successfully created.
          400:
            description: Metric already exists.
          401:
            description: >
                Authorization Required. Request does not contain a
                valid access token.
          500:
            description: An error occurred loading the metrics.
        """

        metrics = MetricList.parser.parse_args()['metrics']

        for data in metrics:

            name = data['name']

            if "." in name:
                data['package'], data['display_name'] = name.split(".")
            else:
                message = "You must provide a full qualified name for" \
                          " the metric, e.g. validate_drp.AM1"

                return {"message": message}

            if MetricModel.find_by_name(name):
                message = "A metric with name `{}` already exist.".format(name)
                return {'message': message}, 400

            metric = MetricModel(**data)

            try:
                metric.save_to_db()
            except Exception as error:

                message = "An error occurred inserting metric "\
                          "`{}`.".format(name)

                return {"message": message, "error": str(error)}, 500

        return {"message": "List of metrics successfully created."}, 201
