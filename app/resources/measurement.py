from flask_restful import Resource, reqparse
from flask_jwt import jwt_required

from ..models import MeasurementModel


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
    parser.add_argument('data',
                        type=str,
                        required=True,
                        help="You must provide the data field."
                        )

    def get(self, job):
        measurement = MeasurementModel.find_by_job(job)
        if measurement:
            return measurement.json()
        return {'message': 'Measurement not found.'}, 404

    @jwt_required()
    def post(self, job):

        data = Measurement.parser.parse_args()

        measurement = MeasurementModel(data['metric_name'], job,
                                       data['value'], data['data'])

        try:
            measurement.save_to_db()
        except:
            return {"message": "An error occurred inserting the "
                               "measurement."}, 500

        return measurement.json(), 201

    @jwt_required()
    def delete(self, job):
        measurement = MeasurementModel.find_by_job(job)
        if measurement:
            measurement.delete_from_db()

        return {'message': 'Measurement deleted.'}

    @jwt_required()
    def put(self, job):
        data = Measurement.parser.parse_args()

        measurement = MeasurementModel.find_by_job(job)

        if measurement:
            measurement.value = data['value']
        else:
            measurement = MeasurementModel(job, data['value'],
                                           data['metric_id'])

        measurement.save_to_db()

        return measurement.json(), 202


class MeasurementList(Resource):
    def get(self):
        return {'measurements': [measurement.json() for measurement
                                 in MeasurementModel.query.all()]}
