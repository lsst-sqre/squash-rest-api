from flask import jsonify
from flask import current_app as app
from flask_restful import Resource

from ..models import MetricModel as Metric


class PackageList(Resource):
    def get(self):
        """
        Retrieve the list of verification packages used in SQuaSH.
        ---
        tags:
          - Apps
        responses:
          200:
            description: Package list successfully retrieved.
        """
        package = Metric.query.values(Metric.package)
        try:
            packages = [p[0] for p in set(package)]
        except StopIteration:
            app.logger.warn("No packages found.")

        return jsonify({'packages': packages})
