"""Write SQuaSH data to InfluxDB."""

__all__ = ["Formatter"]

import logging
from datetime import datetime

import requests
from dateutil.parser import parse
from pytz import UTC
from requests.exceptions import ConnectionError, HTTPError

logger = logging.getLogger("squash")


class Formatter:
    """Format methods used by the InfluxDB task.

    Parameters
    ----------
    squash_api_url : `str`
        URL for the SQuaSH API.
    """

    def __init__(self, squash_api_url):
        self.squash_api_url = squash_api_url

    @staticmethod
    def format_timestamp(date):
        """Format timestamp as required by the InfluxDB line protocol.

        Parameters
        ----------
        date : `str`
            Timestamp string

        Returns
        -------
        timestamp : `int`
            Timestamp in nanosecond-precision Unix time.
            See https://docs.influxdata.com/influxdb/v1.6/write_protocols/
        """
        epoch = UTC.localize(datetime.utcfromtimestamp(0))

        timestamp = int((parse(date) - epoch).total_seconds() * 1e9)

        return timestamp

    @staticmethod
    def format_link(text, url):
        """Format a markdown link.

        Parameters
        ----------
        text : `str`
            The link text.
        url : `str`
            The link destination.

        Returns
        -------
            link : `str`
            A markdown formatted link.
        """
        link = f"[{text}]({url})"
        return link

    def get_code_changes(self, ci_id, ci_name):
        """Get code_changes from the SQuaSH API.

        Parameters
        ----------
        ci_id : `str`
            ID of the Jenkins CI run
        ci_name : `str`
            Name of the CI pipeline

        Returns
        -------
        code_changes : `list`
            A list of software packages that changed with respect to the
            previous CI run.
        """
        url = f"{self.squash_api_url}/code_changes/{ci_id}?ci_name={ci_name}"
        try:
            r = requests.get(url)
            r.raise_for_status()
        except HTTPError:
            message = "Could not get code_changes from the SQuaSH API."
            logger.error(message)
        except ConnectionError:
            message = (
                f"Failed to establish connection with the SQuaSH API."
                f"{url}."
            )
            logger.error(message)

        code_changes = r.json()
        return code_changes

    def format_code_changes(self, ci_id, ci_name):
        """Format list of code changes.

        Parameters
        ----------
        ci_id : `str`
            ID of the Jenkins CI run
        ci_name : `str`
            Name of the CI pipeline

        Returns
        -------
        formatted_code_changes : `str`
            Formatted list of packages.
        """
        code_changes = self.get_code_changes(ci_id, ci_name)

        formatted_code_changes = []
        for pkg in code_changes["packages"]:
            name = pkg[0]
            git_sha = pkg[1]
            git_url = pkg[2]
            git_commit_url = git_url.replace(".git", "/commit/") + git_sha
            formatted_url = Formatter.format_link(name, git_commit_url)
            formatted_code_changes.append(formatted_url)

        return ", ".join(formatted_code_changes)

    def format_code_changes_counts(self, ci_id, ci_name):
        """Format code change counts.

        Parameters
        ----------
        ci_id : `str`
            ID of the Jenkins CI run
        ci_name : `str`
            Name of the CI pipeline

        Returns
        -------
        code_changes_counts : `str`
            Formatted list of packages.
        """
        code_changes = self.get_code_changes(ci_id, ci_name)

        code_changes_counts = 0
        if code_changes["counts"]:
            code_changes_counts = code_changes["counts"]

        return code_changes_counts

    @staticmethod
    def sanitize(obj) -> str:
        """Sanitize an InfluxDB tag key, tag value or a field key.

        See https://docs.influxdata.com/influxdb/v0.13/write_protocols/
        write_syntax/#escaping-characters

        Parameters
        ----------
        obj : `obj`
            An object representing the tag key, tag value or field key.

        Returns
        -------
        s : `str`
            A valid string for the tag key, tag value or field key.
        """
        s = str(obj)
        s = s.replace(" ", "_")
        s = s.replace(",", r"\,")
        s = s.replace("=", r"\=")

        return s

    @staticmethod
    def format_influxdb_line(measurement, tags, fields, timestamp):
        """Format a line following the InfluxDB line protocol.

        Parameters
        ----------
        measurement : `str`
            Name of the InfluxDB measurement
        tags : `list`
            A list of valid InfluxDB tags
        fields : `list`
            A list of valid InfluxDB fields
        timestamp : `int`
            A timestamp in nanosecond-precision Unix time.

        Returns
        -------
        line : `str`
            An InfluxDB line as defined by the line protocol in
            https://docs.influxdata.com/influxdb/v1.8/write_protocols/
        """
        line = f"{measurement},{','.join(tags)} {','.join(fields)} {timestamp}"

        return line
