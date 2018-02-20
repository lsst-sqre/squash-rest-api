from flask import jsonify
from flask import current_app as app
from flask_restful import Resource

from ..models import JobModel as Job


class DatasetList(Resource):
    def get(self):
        """
        Retrieve the list of datasets used in SQuaSH.
        ---
        tags:
          - Apps
        responses:
          200:
            description: Dataset list successfully retrieved.
        """
        dataset = Job.query.values(Job.ci_dataset)
        try:
            datasets = [d[0] for d in set(dataset)]
        except StopIteration:
            app.logger.warn("No datasets found.")

        return jsonify({'datasets': datasets})
