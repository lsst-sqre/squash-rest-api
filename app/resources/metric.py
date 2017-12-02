from flask_restful import Resource

from ..models import MetricModel


class Metric(Resource):
    def get(self, name):
        metric = MetricModel.find_by_name(name)
        if metric:
            return metric.json()
        return {'message': 'Metric not found'}, 404

    def post(self, name):
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
        metric = MetricModel.find_by_name(name)
        if not metric:
            return {"message": "Metric {} does not exist.".format(name)}

        metric.delete_from_db()
        return {'message': 'Metric deleted.'}


class MetricList(Resource):
    def get(self):
        return {'metrics': [metric.json() for metric
                            in MetricModel.query.all()]}
