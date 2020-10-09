"""Implement Celery task to write SQuaSH metrics to InfluxDB."""

__all__ = [
    "create_influxdb_database",
    "write_influxdb_line",
    "job_to_influxdb",
]

import logging
import os

import requests
from requests.exceptions import ConnectionError, HTTPError

from .celery import celery
from .utils.transformation import Transformer

INFLUXDB_API_URL = os.environ.get("INFLUXDB_API_URL")
INFLUXDB_DATABASE = os.environ.get("INFLUXDB_DATABASE")
SQUASH_API_URL = os.environ.get("SQUASH_API_URL")

logger = logging.getLogger("squash")


def create_influxdb_database(influxdb_database, influxdb_api_url):
    """Create a database in InfluxDB."""
    params = {"q": f'CREATE DATABASE "{influxdb_database}"'}

    try:
        r = requests.post(url=f"{influxdb_api_url}/query", params=params)
        r.raise_for_status()
    except HTTPError:
        message = f"Could not create InfluxDB database {influxdb_database}."
        logger.error(message)
    except ConnectionError:
        message = f"Failed to establish connection with {influxdb_api_url}."
        logger.error(message)

    return r.status_code


def write_influxdb_line(line, influxdb_database, influxdb_api_url):
    """Write a line to InfluxDB.

    Parameters
    ----------
    line : `str`
        An InfluxDB line formatted according to the line protocol:
        See https://docs.influxdata.com/influxdb/v1.6/write_protocols/

    Returns
    -------
    status_code : `int`
        Status code from the InfluxDB HTTP API.
        204: The request was processed successfully
        400: Malformed syntax or bad query
    """
    params = {"db": influxdb_database}

    url = f"{influxdb_api_url}/write"
    try:
        r = requests.post(url=url, params=params, data=line)
        r.raise_for_status()
    except HTTPError:
        message = f"Could not write line to InfluxDB {line}."
        logger.error(message)
    except ConnectionError:
        message = f"Failed to establish connection with {influxdb_api_url}."
        logger.error(message)

    return r.status_code


@celery.task(bind=True)
def job_to_influxdb(self, job_id):
    """Transform a SQuaSH job into InfluxDB lines and send to InfluxDB.

    Parameters
    ----------
    job_id : `int`
        ID for the SQuaSH job

    Returns
    -------
    status_code : `int`
        Status code from the InfluxDB or SQuaSH APIs
        200 or 204: The request was processed successfully
        400: Malformed syntax or bad query
    """
    status_code = create_influxdb_database(INFLUXDB_DATABASE, INFLUXDB_API_URL)

    if status_code != 200:
        message = "Could not create InfluxDB database."
        return message, status_code

    # Get job data from the SQuaSH API
    url = f"{SQUASH_API_URL}/job/{job_id}"

    try:
        r = requests.get(url=url)
        r.raise_for_status()
    except HTTPError:
        message = f"Could not get job {job_id} from the SQuaSH API."
        logger.error(message)
    except ConnectionError:
        message = f"Failed to establish connection with {SQUASH_API_URL}."
        logger.error(message)

    status_code = r.status_code

    if status_code != 200:
        message = f"Could not get job {job_id} from the SQuaSH API."
        return message, status_code

    data = r.json()
    transformer = Transformer(squash_api_url=SQUASH_API_URL, data=data)

    influxdb_lines = transformer.to_influxdb_line()

    for line in influxdb_lines:
        status_code = write_influxdb_line(
            line, INFLUXDB_DATABASE, INFLUXDB_API_URL
        )

        if status_code != 204:
            message = f"Error writing job {job_id} to InfluxDB."
            return message, status_code

    message = f"Job {job_id} sucessfully written to InfluxDB."
    return message, status_code
