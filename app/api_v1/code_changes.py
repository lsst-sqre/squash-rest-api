from flask_restful import Resource, reqparse
from app.decorators import time_this

from ..models import JobModel as Job
from ..models import EnvModel as Env


class CodeChanges(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('ci_id')

    @time_this
    def get_current(self, ci_id):
        """ Given the ci_id returns the corresponding job object.
        """
        env = Env.find_by_name(env_name='jenkins')
        current = Job.find_by_env_data(env_id=env.id, key='ci_id', value=ci_id)

        return current

    @time_this
    def get_previous(self, ci_id):
        """ Given the ci_id returns the job corresponding to the
        previous ci_id.
        """
        queryset = Job.query.order_by(Job.date_created.asc())
        resultset = queryset.values(Job.env['ci_id'])

        ci_ids = []
        for result in resultset:
            if result[0] not in ci_ids:
                ci_ids.append(result[0])

        index = 0
        if ci_id in ci_ids:
            index = ci_ids.index(ci_id)

        if index == 0:
            previous = None
        else:
            expression = Job.env['ci_id'] == ci_ids[index - 1]
            previous = queryset.filter(expression).first()

        return previous

    @time_this
    def compute_code_changes(self, previous, current):
        """ Return the packages in the current job that changed
            wrt the previous job.

            Notes
            -----
            The code changes are computed like this:

            - packages present in the current job but not
            in the previous one
            - packages present in the previous job but
            removed in the current one
            - packages present in both but the git commit
            sha has change

            Parameters
            ----------
            previous: Job object
                Job object containing the previous job
            current: Job object
                Job object containing the current job

            Return
            ------
            code_changes:
                dictionary with the the packages that changed and the
                number of packages that changed.
        """
        code_changes = {'packages': [], 'counts': []}

        prev_pkgs = set([(p.name, p.git_sha, p.git_url)
                        for p in previous.packages])

        curr_pkgs = set([(p.name, p.git_sha, p.git_url)
                        for p in current.packages])

        diff_pkgs = list(curr_pkgs.difference(prev_pkgs))

        if diff_pkgs:
            code_changes = {'packages': diff_pkgs, 'counts': len(diff_pkgs)}

        return code_changes

    @time_this
    def get(self):
        """
        Retrieve the list of packages that changed wrt to the
        previous job.
        ---
        tags:
          - Apps
        parameters:
        - name: ci_dataset
          in: url
          type: string
          description: >
            Name of the data set used in this job, e.g: cfht, decam, hsc
        - name: filter_name
          in: url
          type: string
          description: >
            Name of the filter associated to a given dataset, e.g 'r'
            for cfht
        - name: period
          in: url
          type: string
          description: >
             The period used to retrieve the data, e.g: "Last Month",
             "Last 6 Months", "Last Year" or "All". By default retrieves
             the last month of data.
        responses:
          200:
            description: List of packages successfully retrieved.
        """
        args = self.parser.parse_args()

        code_changes = {'packages': [], 'counts': []}
        ci_id = args['ci_id']
        if ci_id:
            current = self.get_current(ci_id)
            previous = self.get_previous(ci_id)

            if previous:
                code_changes = self.compute_code_changes(previous, current)

        return {'ci_id': ci_id,
                'packages': code_changes['packages'],
                'counts': code_changes['counts']}
