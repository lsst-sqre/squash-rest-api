from flask_restful import Resource, reqparse

from ..models import MetricModel


class Metric(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('description',
                        type=str,
                        required=True,
                        help="You must provide a description text associated "
                             "to this metric."
                        )
    parser.add_argument('unit',
                        type=str
                        )
    # accept multiple values
    # http://flask-restful.readthedocs.io/en/0.3.5/reqparse.html
    parser.add_argument('tags',
                        type=str, action="append")
    parser.add_argument('reference',
                        type=dict)

    def get(self, name):
        """
        Retrieve a single metric from SQuaSH
        ---
        tags:
          - Metric
        parameters:
        - name: name
          in: path
          description: Name of the metric
          required: true
        responses:
          200:
            description: Metric found
          404:
            description: Metric not found
        """
        metric = MetricModel.find_by_name(name)
        if metric:
            return metric.json()
        return {'message': 'Metric not found'}, 404

    def post(self, name):
        """
        Create a single SQuaSH metric
        ---
        tags:
          - Metric
        parameters:
        - name: name
          in: path
          description: Name of the metric
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
            description: Metric successfully created
          400:
            description: A metric whit this name already exists
          500:
            description: An error occurred creating this metric
        """
        if MetricModel.find_by_name(name):
            return {'message': "A metric with name '{}' already "
                               "exists.".format(name)}, 400

        data = Metric.parser.parse_args()

        metric = MetricModel(name, data['description'], data['unit'],
                             data['tags'], data['reference'])
        try:
            metric.save_to_db()
        except:
            return {"message": "An error occurred creating "
                               "metric '{}'.".format(name)}, 500

        return metric.json(), 201

    def delete(self, name):
        """
        Delete a single SQuaSH metric
        ---
        tags:
          - Metric
        parameters:
        - name: name
          in: path
          description: metric name
          required: true
        responses:
          200:
            description: Metric deleted
          400:
            description: Metric does not exist
        """
        metric = MetricModel.find_by_name(name)
        if not metric:
            return {"message": "Metric {} does not exist.".format(name)}

        metric.delete_from_db()
        return {'message': 'Metric deleted.'}


class MetricList(Resource):
    def get(self):
        """
        Retrieve the complete list of SQuaSH metrics
        ---
        tags:
          - Metrics
        responses:
          200:
            description: List of SQuaSH metrics
        """
        return {'metrics': [metric.json() for metric
                            in MetricModel.query.all()]}
