from flask_restful import Resource


class Version(Resource):
    def get(self):
        """
        Retrieve the default version of the API.
        ---
        tags:
          - Misc
        responses:
          200:
            description: Version successfully retrieved
        """
        return {"version": "1.0"}
