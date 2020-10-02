from flask import jsonify
from flask_restful import Resource

from squash.tasks.s3 import upload_object


class Status(Resource):
    def get(self, task_id):
        """
        Retrieve status of an upload task.
        ---
        tags:
          - Misc
        parameters:
        - name: task_id
          in: path
          type: string
          description: Upload task ID as returned by /job
          required: true
        responses:
          200:
            description: >
                Upload task status successfully retrieved.
                PENDING: the task did not start yet.
                STARTED: the task has started.
                SUCCESS: the task has completed.
                FAILURE: something went wrong.

        """
        task = upload_object.AsyncResult(task_id)

        if task.state == "PENDING":
            # Upload task did not start yet
            response = {
                "status": task.state,
            }

        elif task.state != "FAILURE":
            response = {
                "status": task.state,
            }
        else:
            # Something went wrong in
            response = {"status": task.state, "message": str(task.info)}
        return jsonify(response)
