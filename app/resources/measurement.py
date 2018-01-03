from flask_restful import Resource, reqparse
from flask_jwt import jwt_required

from ..models import MeasurementModel, JobModel, MetricModel


class Measurement(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('value',
                        type=float,
                        required=True,
                        help="This field cannot be left blank."
                        )
    parser.add_argument('unit',
                        type=str,
                        required=True,
                        help="This field cannot be left blank."
                        )
    parser.add_argument('metric',
                        type=str,
                        required=True,
                        help="You must provide a metric name associated "
                             "to the measurement."
                        )

    def get(self, job_id):
        """
        Retrieve all measurements performed by a verification job.
        ---
        tags:
          - Metric Measurements
        parameters:
        - name: job_id
          in: path
          type: integer
          description: ID of the job.
          required: true
        responses:
          200:
            description: List of Measurements successfully retrieved.
          404:
            description: Job not found.
        """

        # find the corresponding job
        job = JobModel.find_by_id(job_id)

        if job:
            # find the associated measurements
            measurements = MeasurementModel.find_by_job_id(job.id)

            return {'measurements': [measurement.json() for measurement
                                     in measurements]}
        else:
            message = 'Job `{}` not found.'.format(job_id)

            return {'message': message}, 404

    @jwt_required()
    def post(self, job_id):
        """
        Create a new measurement for an existing job.
        ---
        tags:
          - Metric Measurements
        parameters:
        - name: job_id
          in: path
          type: integer
          description: ID of the job.
          required: true
        - in: body
          name: "Request body:"
          schema:
            type: object
            required:
              - metric
              - value
              - unit
            properties:
              metric:
                type: string
              value:
                type: number
              unit:
                type: string
        responses:
          201:
            description: Measurement successfully created.
          401:
            description: >
                Authorization Required. Request does not contain a
                valid access token.
          404:
            description: Job or associated metric not found.
          500:
            description: An error occurred inserting the measurement.
        """

        data = Measurement.parser.parse_args()

        # find the corresponding job
        job = JobModel.find_by_id(job_id)

        if job:
            metric_name = data['metric']
            # find the associated metric
            metric = MetricModel.find_by_name(metric_name)
        else:
            message = "Job `{}` not found.".format(job_id)
            return {'message': message}, 404

        if metric:
            measurement = MeasurementModel(job.id, metric.id, **data)
        else:
            message = "Metric `{}` not found.".format(metric_name)
            return {'message': message}, 404

        try:
            measurement.save_to_db()
        except:
            return {"message": "An error occurred inserting the "
                               "measurement."}, 500

        return measurement.json(), 201


class MeasurementList(Resource):
    def get(self):
        """
        Retrieve the complete list of measurements.
        ---
        tags:
          - Metric Measurements
        responses:
          200:
            description: List of Measurements successfully retrieved.
        """
        return {'measurements': [measurement.json() for measurement
                                 in MeasurementModel.query.all()]}
