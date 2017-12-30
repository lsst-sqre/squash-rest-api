from flask_restful import Resource, reqparse

from ..models import MetricModel


class Metric(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('description',
                        type=str,
                        required=True,
                        help="You must provide the package name associated "
                             "to this metric."
                        )
    parser.add_argument('package',
                        type=str
                        )
    parser.add_argument('unit',
                        type=str
                        )
    # accept multiple values
    # http://flask-restful.readthedocs.io/en/0.3.5/reqparse.html
    parser.add_argument('tags',
                        type=str, action="append"
                        )
    parser.add_argument('reference',
                        type=dict
                        )

    def get(self, name):
        """
        Retrieve a metric from its name.
        ---
        tags:
          - Metrics
        parameters:
        - name: name
          in: path
          type: string
          description: Full qualified name of the metric, e.g. validate_drp.AM1
          required: true
        responses:
          200:
            description: Metric found
          404:
            description: Metric not found
        """
        metric = MetricModel.find_by_name(name)

        if metric:
            return metric.json()

        return {'message': 'Metric not found'}, 404

    def post(self, name):
        """
        Create a metric.
        ---
        tags:
          - Metrics
        parameters:
        - name: name
          in: path
          type: string
          description: Full qualified name of the metric, e.g. validate_drp.AM1
          required: true
        - in: body
          name: "Request body:"
          schema:
            type: object
            required:
              - description
            properties:
              description:
                type: string
              unit:
                type: string
              tags:
                type: array
              reference:
                type: object
        responses:
          201:
            description: Metric successfully created
          400:
            description: A metric with this name already exists
          500:
            description: An error occurred creating this metric
        """

        data = Metric.parser.parse_args()

        if "." in name:
            data['package'], data['display_name'] = name.split(".")
        else:
            message = "You must provide a full qualified name for" \
                      " the metric, e.g. validate_drp.AM1"

            return {"message": message}

        # Metric names are unique
        if MetricModel.find_by_name(name):

            message = "A metric with name `{}` already exist.".format(name)
            return {'message': message}, 400

        metric = MetricModel(name, **data)

        try:
            metric.save_to_db()
        except:

            message = "An error ocurred creating metric `{}`.".format(name)
            return {"message": message}, 500

        return metric.json(), 201

    def delete(self, name):
        """
        Delete a metric.
        ---
        tags:
          - Metrics
        parameters:
        - name: name
          in: path
          type: string
          description: Full qualified name of the metric, e.g. validate_drp.AM1
          required: true
        responses:
          200:
            description: Metric deleted
          400:
            description: Metric does not exist
        """

        metric = MetricModel.find_by_name(name)
        if not metric:
            return {"message": "Metric '{}' does not "
                               "exist.".format(name)}

        metric.delete_from_db()
        return {'message': 'Metric deleted.'}


class MetricList(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("metrics",
                        type=dict,
                        action="append"
                        )

    def get(self):
        """
        Retrieve the complete list of metrics.
        ---
        tags:
          - Metrics
        responses:
          200:
            description: List of metrics successfully retrieved
        """
        return {'metrics': [metric.json() for metric
                            in MetricModel.query.all()]}

    def post(self):
        """
        Create a list of metrics.
        ---
        tags:
          - Metrics
        parameters:
        - name: "Request body:"
          in: body
          schema:
            type: object
            required:
              - metrics
            properties:
              metrics:
                type: array
        responses:
          201:
            description: List of metrics successfully loaded
          400:
            description: Metric already exists
          500:
            description: An error occurred loading the metrics
        """

        metrics = MetricList.parser.parse_args()['metrics']

        for data in metrics:

            name = data['name']

            if "." in name:
                data['package'], data['display_name'] = name.split(".")
            else:
                message = "You must provide a full qualified name for" \
                          " the metric, e.g. validate_drp.AM1"

                return {"message": message}

            if MetricModel.find_by_name(name):
                message = "A metric with name `{}` already exist.".format(name)
                return {'message': message}, 400

            metric = MetricModel(**data)

            try:
                metric.save_to_db()
            except Exception as error:

                message = "An error occurred inserting metric "\
                          "`{}`.".format(name)

                return {"message": message, "error": str(error)}, 500

        return {"message": "List of metrics successfully loaded."}
