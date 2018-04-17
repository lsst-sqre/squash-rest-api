from flask_restful import Resource, reqparse
from flask_jwt import jwt_required

from ..models import SpecificationModel, MetricModel


class Specification(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('threshold',
                        type=dict
                        )
    # accept multiple values
    # http://flask-restful.readthedocs.io/en/0.3.5/reqparse.html
    parser.add_argument('tags',
                        type=str, action="append"
                        )
    parser.add_argument('metadata_query',
                        type=dict
                        )

    def get(self, name):
        """
        Retrieve a metric specification.
        ---
        tags:
          - Metric Specifications
        parameters:
        - name: name
          in: path
          type: string
          description: >
            Full qualified name of the metric specification, e.g.
            validate_drp.AM1.minimum_gri
          required: true
        responses:
          200:
            description: Metric specification found.
          404:
            description: Metric specification not found.
        """
        spec = SpecificationModel.find_by_name(name)
        if spec:
            return spec.json()
        return {'message': 'Metric specification not found'}, 404

    @jwt_required()
    def post(self, name):
        """
        Create a metric specification.
        ---
        tags:
          - Metric Specifications
        parameters:
        - name: name
          in: path
          type: string
          description: >
            Full qualified name of the metric specification, e.g.
            validate_drp.AM1.mininum_gri
          required: true
        - in: body
          name: "Request body:"
          schema:
            type: object
            properties:
              threshold:
                type: object
              tags:
                type: array
              metadata_query:
                type: object
        responses:
          201:
            description: Metric specification successfully created.
          400:
            description: A metric specification whit this name already exists.
          401:
            description: >
                Authorization Required. Request does not contain a
                valid access token.
          500:
            description: An error occurred creating this metric specification.
        """

        data = Specification.parser.parse_args()

        if '.' in name:
            metric_name = name.rsplit('.', 1)[0]
        else:
            message = "You must provide a full qualified name for the" \
                      " specification, e.g. validate_drp.AM1.minimum_gri."

            return {"message": message}

        # Check if the associated metric exists
        metric = MetricModel.find_by_name(metric_name)

        if metric:
            metric_id = metric.id
        else:

            message = "Metric `{}` not found. You must provide a valid " \
                      "name for the metric associated with this " \
                      "specification.".format(metric_name)

            return {"message": message}, 404

        if SpecificationModel.find_by_name(name):

            message = "A specification with name `{}` already " \
                      "exist.".format(name)

            return {'message': message}, 400

        spec = SpecificationModel(name, metric_id, **data)

        try:
            spec.save_to_db()
        except:

            message = "An error ocurred creating this metric " \
                      "specification".format(name)

            return {"message": message}, 500

        return spec.json(), 201

    @jwt_required()
    def delete(self, name):
        """
        Delete a metric specification.
        ---
        tags:
          - Metric Specifications
        parameters:
        - name: name
          in: path
          type: string
          description: >
            Full qualified name of the metric specification, e.g.
            validate_drp.AM1.mininum_gri
          required: true
        responses:
          200:
            description: Metric specification deleted.
          401:
            description: >
                Authorization Required. Request does not contain a
                valid access token.
          404:
            description: Metric specification not found.
        """
        spec = SpecificationModel.find_by_name(name)

        if not spec:
            message = "The metric specification `{}` not " \
                      "found.".format(name)
            return {"message": message}, 404

        spec.delete_from_db()
        return {'message': 'Metric specification deleted.'}


class SpecificationList(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("specs",
                        type=dict,
                        action="append"
                        )
    parser.add_argument('metric')

    def get(self):
        """
        Retrieve the complete list of metric specifications.
        ---
        tags:
          - Metric Specifications
        parameters:
          - name: metric
            in: url
            type: string
            description: >
                A full qualified name for the Metric,
                e.g `validate_drp.AM1`
        responses:
          200:
            description: List of metric specifications successfully retrieved.
        """

        queryset = SpecificationModel.query.join(MetricModel)

        args = self.parser.parse_args()

        metric = args['metric']

        if metric:
            queryset = queryset.filter(MetricModel.name == metric)

        return {'specs': [spec.json() for spec
                          in queryset.all()]}

    @jwt_required()
    def post(self):
        """
        Create a list of metric specifications.
        ---
        tags:
          - Metric Specifications
        parameters:
        - name: "Request body:"
          in: body
          schema:
            type: object
            required:
              - specs
            properties:
              specs:
                type: array
        responses:
          201:
            description: List of metric specifications successfully created.
          400:
            description: >
                Metric specification already exists or associated metric
                not found.
          401:
            description: >
                Authorization Required. Request does not contain a
                valid access token.
          500:
            description: An error occurred creating a metric specification.
        """

        specs = SpecificationList.parser.parse_args()['specs']

        for data in specs:
            name = data.pop('name')

            if '.' in name:
                metric_name = name.rsplit('.', 1)[0]
            else:
                message = "You must provide a full qualified name for the" \
                          " specification, e.g. validate_drp.AM1.minimum_gri."

                return {"message": message}

            metric = MetricModel.find_by_name(metric_name)

            if metric:
                metric_id = metric.id
            else:
                continue
                message = "Metric `{}` not found. You must provide a valid " \
                          "name for the metric associated with this " \
                          "specification.".format(metric_name)

                return {"message": message}, 400

            if SpecificationModel.find_by_name(name):
                message = "A specification with name `{}` already " \
                          "exist.".format(name)

                return {'message': message}, 400

            spec = SpecificationModel(name, metric_id, **data)

            try:
                spec.save_to_db()
            except:

                message = "An error ocurred creating this metric " \
                          "specification".format(name)

                return {"message": message}, 500

        return {"message": "List of metric specificationss successfully "
                           "created."}, 201
