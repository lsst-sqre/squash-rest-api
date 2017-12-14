from flask_restful import Resource, reqparse

from ..models import SpecificationModel, MetricModel


class Specification(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('package',
                        type=str,
                        required=True,
                        help="You must provide the package name associated "
                             "to this specification."
                        )
    parser.add_argument('metric_name',
                        type=str,
                        required=True,
                        help="You must provide the name of the metric"
                             " associated to this specification."
                        )
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
        Retrieve a single metric specification
        ---
        tags:
          - Specifications
        parameters:
        - name: name
          in: path
          description: name of the metric
          required: true
        responses:
          200:
            description: Metric specification found
          404:
            description: Metric specification not found
        """
        spec = SpecificationModel.find_by_name(name)
        if spec:
            return spec.json()
        return {'message': 'Metric specification not found'}, 404

    def post(self, name):
        """
        Create a metric specification
        ---
        tags:
          - Specifications
        parameters:
        - name: name
          in: path
          description: name of the metric specification
          required: true
        - in: body
          name: "Request body:"
          schema:
            type: object
            required:
              - metric_name
                package
            properties:
              metric_name:
                type: string
              package:
                type: string
              threshold:
                type: object
              tags:
                type: array
              metadata_query:
                type: object
        responses:
          201:
            description: Metric specification successfully created
          400:
            description: A metric specification whit this name already exists
          500:
            description: An error occurred creating this metric specification
        """

        data = Specification.parser.parse_args()

        package = data['package']
        metric_name = data['metric_name']

        # Check if the associated package.metric exists
        metric = MetricModel.find_by_fqn(package, metric_name)

        if metric:
            metric_id = metric.id
        else:
            return {'message': 'Metric {}.{} not found. You must provide a '
                               'valid package and metric name to associtate '
                               'with this '
                               'specification.'.format(package,
                                                       metric_name)}, 404

        if SpecificationModel.find_by_name(name):
            return {'message': "A specification with name '{}' already "
                               "exists.".format(name)}, 400

        spec = SpecificationModel(name, metric_id,
                                  data['threshold'], data['tags'],
                                  data['metadata_query'])
        try:
            spec.save_to_db()
        except:
            return {"message": "An error occurred creating "
                               "metric specification '{}'.".format(name)}, 500

        return spec.json(), 201

    def delete(self, name):
        """
        Delete a single metric specification
        ---
        tags:
          - Specifications
        parameters:
        - name: name
          in: path
          description: name of the metric specification
          required: true
        responses:
          200:
            description: Metric specification deleted
          400:
            description: Metric specification does not exist
        """
        spec = SpecificationModel.find_by_name(name)
        if not spec:
            return {"message": "Metric specification {} does "
                               "not exist.".format(name)}

        spec.delete_from_db()
        return {'message': 'Metric specification deleted.'}


class SpecificationList(Resource):
    def get(self):
        """
        Retrieve the complete list of metric specifications
        ---
        tags:
          - Specifications
        responses:
          200:
            description: List of metric specifications successfully retrieved
        """
        return {'specifications': [spec.json() for spec
                                   in SpecificationModel.query.all()]}
