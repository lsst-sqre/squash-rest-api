"""Implement Celery task to write SQuaSH metrics to InfluxDB."""

__all__ = ["send_to_influxdb", "job_to_influxdb"]

import os

import requests

from .celery import celery

INFLUXDB_API_URL = os.environ.get("INFLUXDB_API_URL")
INFLUXDB_DATABASE = os.environ.get("INFLUXDB_DATABASE")
SQUASH_API_URL = os.environ.get("SQUASH_API_URL")


def send_to_influxdb(influxdb_line):
    """Send an InfluxDB line to InfluxDB.

    Parameters
    ----------
    influxdb_line: `<str>`
        An InfluxDB line as defined by the line protocol in
        https://docs.influxdata.com/influxdb/v1.6/write_protocols/

    status_code: `<int>`
        Status code from the InfluxDB HTTP API.
        204:
            The request was processed successfully
        400:
            Malformed syntax or bad query
    """
    params = {"db": INFLUXDB_DATABASE}
    r = requests.post(
        url=INFLUXDB_API_URL + "/write", params=params, data=influxdb_line
    )

    return r.status_code


@celery.task(bind=True)
def job_to_influxdb(self, job_id, date_created, data):
    """Transform a SQuaSH job into InfluxDB lines and send to InfluxDB.

    Parameters
    ----------
    job_id: `int`
        Id for the SQuaSH job

    Returns
    -------
    status_code: `int`
        Status code from the InfluxDB HTTP API.
        204:
            The request was processed successfully
        400:
            Malformed syntax or bad query
    """
    # The datamodel for a SQuaSH job in InfluxDB maps each verification package
    # to an InfluxDB measurement, verification job metadata to InfluxDB
    # tags and metric names and values to fields.

    # Here we associate metrics (fields) to their corresponding
    # packages (measurements)
    pass
