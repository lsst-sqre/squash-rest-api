from flask_restful import Resource

from ..models import JobModel as Job
from ..models import MetricModel as Metric
from ..models import MeasurementModel as Measurement


class Stats(Resource):
    def get(self):
        """
        Retrieve statistics about verification jobs, metrics and measurements
        ---
        tags:
          - Misc
        responses:
          200:
            description: Statistics successfully retrieved.
        """

        stats = {}

        last_job = Job.query.order_by(Job.id.desc()).first()
        last_job_date = last_job.date_created.strftime("%Y-%m-%d %H:%M:%S")
        number_of_jobs = Job.query.count()
        number_of_metrics = Metric.query.count()
        number_of_measurements = Measurement.query.count()

        stats['last_job_date'] = last_job_date
        stats['number_of_jobs'] = number_of_jobs
        stats['number_of_metrics'] = number_of_metrics
        stats['number_of_measurements'] = number_of_measurements

        return {'stats': stats}
