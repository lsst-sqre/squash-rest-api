from flask_restful import Resource, reqparse
from flask_jwt import jwt_required

from ..models import JobModel, MetricModel, MeasurementModel, PackageModel,\
    BlobModel, EnvModel


class JobWithArg(Resource):
    def get(self, job_id):
        """
        Retrieve a verification job.
        ---
        tags:
          - Jobs
        parameters:
        - name: job_id
          in: path
          type: integer
          description: ID of the job.
          required: true
        responses:
          200:
            description: Job successfully retrieved.
          404:
            description: Job not found.
        """
        job = JobModel.find_by_id(job_id)

        if job:
            return job.json()

        return {'message': 'Job not found'}, 404

    @jwt_required()
    def delete(self, job_id):
        """
        Delete a verification job and associated measurements,\
        data blobs and metadata.
        ---
        tags:
          - Jobs
        parameters:
        - name: job_id
          in: path
          type: integer
          description: ID of the job.
          required: true
        responses:
          200:
            description: Job deleted.
          404:
            description: Job not found.
          401:
            description: >
                Authorization Required. Request does not contain a
                valid access token.
        """

        job = JobModel.find_by_id(job_id)

        if not job:
            message = "Job `{}` does not exist.".format(job_id)
            return {"message": message}, 404

        job.delete_from_db()
        return {'message': 'Job deleted.'}


class Job(Resource):
    parser = reqparse.RequestParser()
    # accept multiple values
    # http://flask-restful.readthedocs.io/en/0.3.5/reqparse.html
    parser.add_argument("measurements",
                        type=dict,
                        default=[],
                        action="append",
                        )
    parser.add_argument("meta",
                        default={},
                        type=dict,
                        )
    parser.add_argument("blobs",
                        type=dict,
                        default=[],
                        action="append",
                        )

    @jwt_required()
    def post(self):
        """
        Create a verification job.
        This is the entry point for `dispatch_verify.py`. \
        See http://sqr-019.lsst.io for the body content.
        ---
        tags:
          - Jobs
        parameters:
        - in: body
          name: "Request body:"
          schema:
            type: object
            required:
              - measurements
              - meta
            properties:
              measurements:
                type: array
              blobs:
                type: array
              meta:
                type: object
        responses:
          201:
            description: Job successfully created.
          400:
            description: Missing or invalid data in the request body.
          401:
            description: >
                Authorization Required. Request does not contain a
                valid access token.
          500:
            description: An error occurred creating this job.
        """

        data = Job.parser.parse_args()

        # Create a job

        # First check if the env exists, if not create it
        if 'env' in data['meta']:
            env = data['meta'].pop('env')
        else:
            message = "Missing env metadata."
            return {'message': message}, 400

        if 'env_name' in env:
            e = EnvModel.find_by_name(env['env_name'])
            if not e:
                e = EnvModel(env['env_name'])
                try:
                    e.save_to_db()
                except Exception as error:
                    message = "An error occurred creating the env object."
                    return {'message': message, 'error': str(error)}, 500
        else:
            message = "Missing `env_name` in env metadata."
            return {"message": message}, 400

        # Now extract the package metadata
        if 'packages' in data['meta']:
            packages = data['meta'].pop('packages')
        else:
            message = "Missing packages metadata."
            return {'message': message}

        # At this point what remains in data['meta'] are
        # arbitrary metadata associated with the job, see
        # tests/verify_job.ipynb for a complete example

        j = JobModel(e.id, env, data['meta'])

        try:
            j.save_to_db()
        except Exception as error:
            message = "An error occurred creating the job object."
            return {'message': message, 'error': str(error)}, 500

        # Insert packages
        if packages:
            for package in packages:
                p = PackageModel(j.id, **packages[package])
                try:
                    p.save_to_db()
                except Exception as error:
                    message = "An error occurred inserting packages for " \
                              "job `{}`.".format(j.id)
                    return {'message': message, 'error': str(error)}, 500

        # Insert measurements
        if 'measurements' in data:
            for measurement in data['measurements']:

                if measurement and 'metric' in measurement:
                    metric_name = measurement['metric']
                else:
                    message = "You must provide a list of measurements" \
                              "and the associated metric name."

                    return {"message": message}, 400

                # If the associated metric is not found return
                metric = MetricModel.find_by_name(metric_name)

                if metric:
                    m = MeasurementModel(j.id, metric.id, **measurement)
                else:
                    message = "Metric `{}` not found, it looks like the " \
                              "metrics definition in SQuaSH is not up to " \
                              "date.".format(metric_name)
                    return {"message": message}, 400

                try:
                    m.save_to_db()
                except Exception as error:
                    message = "An error occurred inserting measurements for " \
                              "job `{}`.".format(j.id)
                    return {'message': message, 'error': str(error)}, 500

        # Insert blobs
        if 'blobs' in data:
            for blob in data['blobs']:
                b = BlobModel(j.id, **blob)
                try:
                    b.save_to_db()
                    print("saving data blob")
                except Exception as error:
                    message = "An error occurred inserting blobs for" \
                              "job `{}`.".format(j.id)
                    return {'message': message, 'error': str(error)}, 500

        message = "Job `{}` successfully created".format(j.id)
        return {'message': message}, 201
