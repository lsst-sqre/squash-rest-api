import datetime

from flask_restful import Resource, reqparse

from ..models import MeasurementModel as Measurement
from ..models import JobModel as Job
from ..models import MetricModel as Metric


class Monitor(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('ci_dataset')
    parser.add_argument('period')

    def get(self):
        """
        Retrieve the data structure used to feed the monitor app.
        ---
        tags:
          - Apps
        parameters:
        - name: ci_dataset
          in: url
          type: string
          description: >
            Name of the data set used in this job, e.g: cfht, decam, hsc
        - name: period
          in: url
          type: string
          description: >
             The period used to retrieve the data, e.g: "Last Month",
             "Last 6 Months", "Last Year" or "All". By default retrieves
             the last month of data.
        responses:
          200:
            description: Monitor data successfully retrieved.
        """

        queryset = Measurement.query.join(Job, Metric)

        args = self.parser.parse_args()

        ci_dataset = args['ci_dataset']

        if ci_dataset:
            queryset = queryset.filter(Job.ci_dataset == ci_dataset)

        period = args['period']

        if period:
            end = datetime.datetime.today()

            # by default shows last month of data
            start = end - datetime.timedelta(weeks=4)

            if period == "Last year":
                start = end - datetime.timedelta(weeks=48)
            elif period == "Last 6 months":
                start = end - datetime.timedelta(weeks=24)
            elif period == "Last 3 months":
                start = end - datetime.timedelta(weeks=12)

            if period != "All":
                queryset = queryset.filter(Job.date_created > start)

        queryset = queryset.order_by(Job.date_created.asc())

        generator = queryset.values(Measurement.value,
                                    Measurement.metric_name,
                                    Metric.package,
                                    Job.date_created,
                                    Job.ci_dataset)

        value_list = []
        metric_name_list = []
        package_list = []
        date_created_list = []
        ci_dataset_list = []

        for value, metric_name, package, date_created, ci_dataset \
                in generator:

            value_list.append(value)
            metric_name_list.append(metric_name)
            package_list.append(package)
            date_created_list.append(date_created.
                                     strftime("%Y-%m-%dT%H:%M:%SZ"))
            ci_dataset_list.append(ci_dataset)

        return {'value': value_list,
                'date_created': date_created_list,
                'package': package_list,
                'metric_name': metric_name_list,
                'ci_dataset': ci_dataset_list}
