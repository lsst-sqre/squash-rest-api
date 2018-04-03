from flask_restful import Resource, reqparse

import itertools

from ..models import JobModel as Job
from ..models import PackageModel as Package


class CodeChanges(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('ci_dataset')

    def pairwise(self, iterable):
        """Create a list of tuple pairs from a list
        l -> (l[0], l[1]), (l[1], l[2]), (l[2], l[3]), ...
        """
        a, b = itertools.tee(iterable)
        next(b, None)
        return zip(a, b)

    def compute_code_changes(self, resultset):
        """
        Return the difference in packages between two CI jobs:
        - packages present in the current job but not
        in the previous one
        - packages present in the previous job but
        removed in the current one
        - packages present in both but the git commit
        sha has change

        Parameters
        ----------
        resultset: dict
            dictionary containing ci_ids, names, git_shas
            and git_urls

        Return
        ------
        code_changes:
            dictionary with the ci_id, the packages difference
            wrt the previous job and the number of packages that
            changed

        """

        # list of unique ci_id's
        ci_ids = []
        for result in resultset:
            ci_id = result[0]
            if ci_id not in ci_ids:
                ci_ids.append(ci_id)

        code_changes = []

        for prev_ci_id, curr_ci_id in self.pairwise(ci_ids):

            # ci_id = p[0]
            # name = p[1]
            # git_sha = p[2]
            # git_url = p[3]

            prev_pkgs = set([(p[1], p[2], p[3])
                             for p in resultset if p[0] == prev_ci_id])

            curr_pkgs = set([(p[1], p[2], p[3])
                             for p in resultset if p[0] == curr_ci_id])

            diff_pkgs = curr_pkgs.difference(prev_pkgs)

            if diff_pkgs:
                code_changes.append({'ci_id': curr_ci_id,
                                     'packages': list(diff_pkgs),
                                     'count': len(diff_pkgs)})

        return code_changes

    def get(self):
        """
        Retrieve the list of packages that changed wrt to the
        previous job.
        ---
        tags:
          - Apps
        responses:
          200:
            description: List of packages successfully retrieved.
        """

        # join job and packages and get ci_id, packages name, git_commit
        # and git_url sorted by date

        queryset = Job.query.join(Package)

        args = self.parser.parse_args()
        ci_dataset = args['ci_dataset']

        if ci_dataset:
            queryset = queryset.filter(Job.ci_dataset == ci_dataset)

        queryset = queryset.order_by(Job.date_created.asc())

        generator = queryset.values(Job.env['ci_id'],
                                    Package.name,
                                    Package.git_sha,
                                    Package.git_url)

        resultset = []

        for result in generator:
            resultset.append(result)

        code_changes = self.compute_code_changes(resultset)

        return {'code_changes': code_changes}
