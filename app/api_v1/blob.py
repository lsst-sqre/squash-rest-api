import json

from app.tasks.s3 import download_object
from flask_restful import Resource, reqparse

from ..models import JobModel as Job


class Blob(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument(
        "metric",
        type=str,
        required=True,
        help="This field cannot be left blank.",
    )

    parser.add_argument(
        "name",
        type=str,
        required=True,
        help="This field cannot be left blank.",
    )

    def get(self, job_id):
        """
        Retrieve a data blob
        ---
        tags:
          - Blobs
        parameters:
        - name: job_id
          in: path
          type: integer
          description: ID of the job from which to retrieve the data blob
          required: true
        - name: metric
          in: url
          type: string
          description: Full qualified name of the metric, e.g. validate_drp.AM1
          required: true
        - name: name
          in: url
          type: string
          description: Name of the data blob, e.g. MatchedMultiVisitDataset
          required: true
        responses:
          200:
            description: Data blob successfully retrieved.
          404:
            description: Data blob not found.
        """
        job = Job.find_by_id(job_id)

        args = self.parser.parse_args()

        metric = args["metric"]

        name = args["name"]

        s3_uri = None
        for meas in job.measurements:

            if meas.metric_name == metric:
                for blob in meas.blobs:

                    if blob.name == name:
                        s3_uri = blob.s3_uri

        data = None
        if s3_uri:
            data = download_object(s3_uri)

        if data:
            return json.loads(data)

        return {"message": "Data blob not found"}, 404
