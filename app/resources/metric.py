from flask_restful import Resource, reqparse

from ..models import MetricModel


class Metric(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('description',
                        type=str,
                        )
    parser.add_argument('package',
                        type=str,
                        required=True,
                        help="You must provide the package name associated "
                             "to this metric."
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
        Retrieve a single metric
        ---
        tags:
          - Metrics
        parameters:
        - name: name
          in: path
          description: name of the metric
          required: true
        responses:
          200:
            description: Metric found
          404:
            description: Metric not found
        """
        metrics = MetricModel.find_by_name(name)

        if metrics:
            return {'metrics': [metric.json() for metric in metrics]}

        return {'message': 'Metric not found'}, 404

    def post(self, name):
        """
        Create a single metric
        ---
        tags:
          - Metrics
        parameters:
        - name: name
          in: path
          description: name of the metric
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
              package:
                type: string
              unit:
                type: string
              tags:
                type: array
              reference:
                type: object
        responses:
          201:
            description: Metric successfully created
          400:
            description: A metric whit this name already exists
          500:
            description: An error occurred creating this metric
        """

        data = Metric.parser.parse_args()

        package = data['package']

        # Metric names are unique inside a package
        if MetricModel.find_by_fqn(package, name):
            return {'message': "A metric with name '{}.{}' already "
                               "exists.".format(package, name)}, 400

        metric = MetricModel(name, data['description'], package,
                             data['unit'], data['tags'], data['reference'])
        try:
            metric.save_to_db()
        except:
            return {"message": "An error occurred creating "
                               "metric '{}'.".format(name)}, 500

        return metric.json(), 201

    def delete(self, name):
        """
        Delete a single metric
        ---
        tags:
          - Metrics
        parameters:
        - name: name
          in: path
          description: name of the metric
          required: true
        - name: package
          in: query
          description: name of the package associated with the metric
          required: true
        responses:
          200:
            description: Metric deleted
          400:
            description: Metric does not exist
        """
        data = Metric.parser.parse_args()
        package = data['package']

        metric = MetricModel.find_by_fqn(package, name)
        if not metric:
            return {"message": "Metric '{}.{}' does not "
                               "exist.".format(package, name)}

        metric.delete_from_db()
        return {'message': 'Metric deleted.'}


class MetricList(Resource):
    def get(self):
        """
        Retrieve the complete list of metrics
        ---
        tags:
          - Metrics
        responses:
          200:
            description: List of SQuaSH metrics successfully retrieved
        """
        return {'metrics': [metric.json() for metric
                            in MetricModel.query.all()]}
