from flask_restful import Resource, reqparse
from sqlalchemy import func

from ..models import JobModel as Job
from ..models import MeasurementModel as Measurement
from ..models import MetricModel as Metric
from ..models import SpecificationModel as Specification


class Kpms(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("job_id")
    parser.add_argument("package")
    parser.add_argument("filter_name")
    parser.add_argument("dataset_name")
    parser.add_argument("metric_tag")
    parser.add_argument("specification_tag")

    def get(self):
        """
        Retrieve the data consumed by the KPMs dashboard.
        ---
        tags:
          - Apps
        parameters:
        - name: job_id
          in: url
          type: string
          description: Job ID for which the KPMs will be retrieved.
        - name: package
          in: url
          type: string
          description: >
             Name of the verification package for which the KPMs will be \
             retrieved. Use this option to get the most recent job for \
             this package. Dot not use this option with job_id.
        - name: filter_name
          in: url
          type: string
          description: >
             Name of the filter for which the KPMs will be \
             retrieved. It looks for the filter name in the job \
             metadata and also in the specification metadata_query. \
             If it is provided only chromatic metrics are returned.
        - name: dataset_name
          in: url
          type: string
          description: >
             Name of the dataset for which the KPMs will be \
             retrieved. It looks for the dataset name in the job \
             metadata and also in the specification metadata_query.
        - name: metric_tag
          in: url
          type: string
          description: Tag used to filter metrics.
        - name: specification_tag
          in: url
          type: string
          description: Tag used to filter specifications.
        responses:
          200:
            description: KPMs data successfully retrieved.
        """

        queryset = Measurement.query.join(Job, Metric, Specification)

        args = self.parser.parse_args()

        job_id = args["job_id"]

        # If job_id is not specified, return results for the most recent job
        # for a given dataset and package
        if not job_id:
            package = args["package"]
            if package:
                queryset = queryset.filter(Metric.package == package)

            last_job = queryset.order_by(Job.id.desc()).first()
            job_id = last_job.id

        queryset = queryset.filter(Job.id == job_id)

        # `dataset_name` is used to select the right metric specification, and
        # also ensures that the job was executed on that dataset

        dataset_name = args["dataset_name"]
        if dataset_name:
            queryset = queryset.filter(Job.ci_dataset == dataset_name)
            expr = Specification.metadata_query["dataset_name"] == dataset_name
            queryset = queryset.filter(expr)

        # `filter_name` corresponds to the name of the filter in the metric
        # specification, if it is provided only chromatic metrics are returned
        filter_name = args["filter_name"]
        if filter_name:
            queryset = queryset.filter(Job.meta["filter_name"] == filter_name)
            # get the corresponding specification for
            expr = Specification.metadata_query["filter_name"] == filter_name
            queryset = queryset.filter(expr)

        metric_tag = args["metric_tag"]
        if metric_tag:
            # https://stackoverflow.com/questions/33513625/
            # invalid-json-text-in-argument-2-json-contains-in-mysql-5-7-8
            expr = func.json_contains(Metric.tags, '"{}"'.format(metric_tag))
            queryset = queryset.filter(expr)

        specification_tag = args["specification_tag"]
        if specification_tag:
            expr = func.json_contains(
                Specification.tags, '"{}"'.format(specification_tag)
            )
            queryset = queryset.filter(expr)

        generator = queryset.values(
            Measurement.value,
            Measurement.metric_name,
            Metric.display_name,
            Metric.tags,
            Specification.name,
            Specification.tags,
            Specification.threshold,
            Specification.metadata_query,
            Job.date_created,
            Job.ci_dataset,
            Job.meta["filter_name"],
            Job.id,
        )

        value_list = []
        metric_name_list = []
        metric_display_name_list = []
        metric_tags_list = []
        spec_name_list = []
        spec_tags_list = []
        spec_threshold_list = []
        spec_metadata_query_list = []
        job_date_created_list = []
        job_dataset_name_list = []
        job_filter_name_list = []
        job_id_list = []

        for (
            value,
            metric_name,
            metric_display_name,
            metric_tags,
            spec_name,
            spec_tags,
            spec_threshold,
            spec_metadata_query,
            job_date_created,
            job_dataset_name,
            job_filter_name,
            job_id,
        ) in generator:

            value_list.append(value)
            metric_name_list.append(metric_name)
            metric_tags_list.append(metric_tags)
            metric_display_name_list.append(metric_display_name)
            spec_name_list.append(spec_name)
            spec_tags_list.append(spec_tags)
            spec_threshold_list.append(spec_threshold)
            spec_metadata_query_list.append(spec_metadata_query)
            formatted_datetime = job_date_created.strftime("%Y-%m-%d %H:%M:%S")
            job_date_created_list.append(formatted_datetime)
            job_dataset_name_list.append(job_dataset_name)
            job_filter_name_list.append(job_filter_name)
            job_id_list.append(job_id)

        return {
            "value": value_list,
            "metric_name": metric_name_list,
            "metric_tags": metric_tags_list,
            "metric_display_name": metric_display_name_list,
            "spec_name": spec_name_list,
            "spec_tags": spec_tags_list,
            "spec_threshold": spec_threshold_list,
            "spec_metadata_query": spec_metadata_query_list,
            "job_date_created": job_date_created_list,
            "job_dataset_name": job_dataset_name_list,
            "job_filter_name": job_filter_name_list,
            "job_id": job_id_list,
        }
