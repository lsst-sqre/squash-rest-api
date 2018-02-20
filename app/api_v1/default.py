from flask import jsonify
from flask import current_app as app
from flask_restful import Resource

from ..models import JobModel as Job
from ..models import MetricModel as Metric
from ..models import SpecificationModel as Spec


class Default(Resource):
    def get(self):
        """
        Retrieve default values used for display configuration \
        in the SQuaSH apps.
        ---
        tags:
          - Apps
        responses:
          200:
            description: Default values successfully retrieved.
        """

        default_dataset = None
        dataset = Job.query.values(Job.ci_dataset)
        try:
            default_dataset = next(dataset)[0]
        except StopIteration:
            app.logger.warn("No dataset found.")

        default_package = None
        package = Metric.query.values(Metric.package)
        try:
            default_package = next(package)[0]
        except StopIteration:
            app.logger.warn("No package found.")

        packages = []
        package = Metric.query.values(Metric.package)
        try:
            packages = [p[0] for p in set(package)]
        except StopIteration:
            app.logger.warn("No package found.")

        metric_list = []
        for package in packages:

            metric_name = Metric.query.filter(Metric.package == package).\
                values(Metric.name)

            try:
                default_metric = next(metric_name)[0]
            except StopIteration:
                app.logger.warn("Could not find metric for `{}`.".
                                format(package))

            metric_list.append({'package': package, 'metric': default_metric})

        metric_name = Metric.query.values(Metric.name)
        try:
            metric_names = [m[0] for m in set(metric_name)]
        except StopIteration:
            app.logger.info("No metric found.")

        spec_list = []
        for metric_name in metric_names:

            default_spec = None
            spec = Spec.query.join(Metric).\
                filter(Metric.name == metric_name).values(Spec.name)
            try:
                default_spec = next(spec)[0]
            except StopIteration:
                app.logger.warn("Could not find specification for `{}`".
                                format(metric_name))

            spec_list.append({'metric': metric_name, 'spec': default_spec})

        default = {'dataset': default_dataset, 'package': default_package,
                   'metric': metric_list, 'spec': spec_list}

        return jsonify({'default': default})
