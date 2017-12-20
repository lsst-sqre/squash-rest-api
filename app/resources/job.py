from flask_restful import Resource, reqparse

from ..models import JobModel, MetricModel, MeasurementModel


class Job(Resource):
    parser = reqparse.RequestParser()
    # accept multiple values
    # http://flask-restful.readthedocs.io/en/0.3.5/reqparse.html
    parser.add_argument('measurements',
                        type=dict,
                        action="append",
                        required=True,
                        help="You must provide a list of measurements associated "
                             "to this job."
                        )
    parser.add_argument('meta',
                        type=dict,
                        required=True,
                        help="You must provide metadata associated to this job"
                        )

    def get(self, ci_id):
        """
        Retrieve a lsst.verify Job from the CI run ID
        ---
        tags:
          - Jobs
        parameters:
        - name: ci_id
          in: path
          description: ID of the CI run
          required: true
        responses:
          200:
            description: Job found
          404:
            description: Job not found
        """
        job = JobModel.find_by_ci_id(ci_id)

        if job:
            return job.json()

        return {'message': 'Job not found'}, 404

    def post(self, ci_id):
        """
        Create an lsst.verify Job
        ---
        tags:
          - Jobs
        parameters:
        - name: ci_id
          in: path
          description: ID of the CI run
          required: true
        - in: body
          name: "Request body:"
          schema:
            type: object
            required:
              - measurements
            properties:
              measurements:
                type: array
              meta:
                type: object
        responses:
          201:
            description: Job successfully created
          400:
            description: >
                A Job with the same CI run ID already exists;
                You must provide a metric name associated with
                measurements
          500:
            description: An error occurred creating this Job
        """

        job = JobModel.find_by_ci_id(ci_id)

        if job:
            return {"message": "Job `{}` already exists.".format(ci_id)}, 400

        data = Job.parser.parse_args()

        # Create a job
        job = JobModel(ci_id, **data['meta'])

        try:
            job.save_to_db()
        except Exception as error:
            message = "An error ocurred creating job `{}`".format(ci_id)
            return {"message": message, "error": str(error)}, 500

        if None in data['measurements']:
            return {"message": "You must provide a list of measurements"
                               " associated to this job."}

        # Insert measurements for this job
        for measurement in data['measurements']:

            if 'metric_name' in measurement:
                metric_name = measurement['metric_name']
            else:
                return {"message": "You must provide a metric name associated "
                                   "with this measurement."}, 400

            # Find the associated metric
            metric = MetricModel.find_by_name(metric_name)

            if metric:
                measurement = MeasurementModel(measurement['value'],
                                               metric.id, job.id)
            else:
                message = "Metric `{}` not found, it looks like an " \
                          "update of the metrics is " \
                          "required.".format(metric_name)

                return {"message": message}, 404

            try:
                measurement.save_to_db()
            except Exception as error:

                message = "An error occurred inserting measurements for " \
                          "job `{}`.".format(ci_id)

                return {"message": message, "error": str(error)}, 500

        # TODO: Insert blobs

        return job.json(), 201


    def delete(self, ci_id):
        """
        Delete a single job, its measurements and data blobs
        ---
        tags:
          - Jobs
        parameters:
        - name: ci_id
          in: path
          description: ID of the CI run
          required: true
        responses:
          200:
            description: Job deleted
          400:
            description: Job does not exist
        """

        job = JobModel.find_by_ci_id(ci_id)

        if not job:
            message = "Job `{}` does not exist.".format(ci_id)

            return {"message": message}

        job.delete_from_db()
        return {'message': 'Job, measurements and blobs deleted.'}


class JobList(Resource):
    def get(self):
        """
        Retrieve the complete list of lsst.verify jobs
        ---
        tags:
          - Jobs
        responses:
          200:
            description: List of jobs successfully retrieved
        """
        jobs = [job.json_summary() for job in JobModel.query.all()]

        return {'jobs': jobs}

