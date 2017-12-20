from flask_restful import Resource, reqparse
# from flask_jwt import jwt_required

from ..models import MeasurementModel, JobModel, MetricModel


class Measurement(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('value',
                        type=float,
                        required=True,
                        help="This field cannot be left blank."
                        )
    parser.add_argument('metric_name',
                        type=str,
                        required=True,
                        help="You must provide a metric name associated "
                             "to the measurement."
                        )

    def get(self, ci_id):
        """
        Retrieve all measurements for this CI run
        ---
        tags:
          - Metric Measurements
        parameters:
        - name: ci_id
          in: path
          description: ID of the CI run
          required: true
        responses:
          200:
            description: List of Measurements successfully retrieved
          404:
            description: Job not found
        """

        # find the corresponding job
        job = JobModel.find_by_ci_id(ci_id)

        if job:
            # find the associated measurements
            measurements = MeasurementModel.find_by_job_id(job.id)

            return {'measurements': [measurement.json() for measurement
                                     in measurements]}
        else:
            message = 'Job `{}` not found.'.format(ci_id)

            return {'message': message}, 404

    # @jwt_required()
    def post(self, ci_id):
        """
       Create a new measurement associated to an existing CI run
       ---
       tags:
         - Metric Measurements
       parameters:
       - name: ci_id
         in: path
         description: ID of the CI run, used to identify a lsst.verify Job
         required: true
       - in: body
         name: "Request body:"
         schema:
           type: object
           required:
             - metric_name
             - value
           properties:
             metric_name:
               type: string
             value:
               type: number
       responses:
         201:
           description: Measurement successfully created
         404:
           description: Associated metric name or job not found
         500:
           description: An error occurred inserting the measurement
       """

        data = Measurement.parser.parse_args()

        # find the corresponding job
        job = JobModel.find_by_ci_id(ci_id)

        if job:
            metric_name = data['metric_name']
            # find the associated metric
            metric = MetricModel.find_by_name(metric_name)
        else:
            message = "Job `{}` not found.".format(ci_id)

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
        Retrieve the complete list of measurements
        ---
        tags:
          - Metric Measurements
        responses:
          200:
            description: List of Measurements successfully retrieved
        """
        return {'measurements': [measurement.json() for measurement
                                 in MeasurementModel.query.all()]}
