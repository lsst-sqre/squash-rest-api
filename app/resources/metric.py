from flask_restful import Resource

from ..models import MetricModel


class Metric(Resource):
    def get(self, name):
        """
        Retrieve a single metric from SQuaSH
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
          description: metric name
          required: true
        responses:
          201:
            description: Metric successfully created
            schema:
              id: Metric
              properties:
                name:
                  type: string
          400:
            description: Metric already exist.
          500:
            description: An error occurred creating the metric
        """
        if MetricModel.find_by_name(name):
            return {'message': "A metric with name '{}' already "
                               "exists.".format(name)}, 400

        metric = MetricModel(name)
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
