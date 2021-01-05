"""Implement Celery task to write SQuaSH metrics to InfluxDB."""

__all__ = [
    "create_influxdb_database",
    "write_influxdb_line",
    "job_to_influxdb",
]

import importlib
import logging
import os

import requests
from requests.exceptions import ConnectionError, HTTPError

from .celery import celery
from .utils.transformation import Transformer

profile = os.environ.get("SQUASH_API_PROFILE", "squash.config.Development")
cls = profile.split(".")[2]
config = getattr(importlib.import_module("squash.config"), cls)()

logger = logging.getLogger("squash")


def create_influxdb_database(
    influxdb_database,
    influxdb_api_url,
    influxdb_username=None,
    influxdb_password=None,
):
    """Create a database in InfluxDB.

    Parameters
    ----------
    influxdb_database: `str`
        Name of the databse to create in InfluxDB.
    influxdb_api_url: `str`
        URL for the InfluxDB HTTP API.
    influxdb_username: `str`
        InfluxDB username, by default set from the INFLUXDB_USERNAME env var.
    influxdb_password: `str`
        InfluxDB password, by default set from the INFLUXDB_PASSWORD env var.

    Returns
    -------
    status_code: `int`
        Status code from the InfluxDB HTTP API.
        200: The request was processed successfully.
        400: Malformed syntax or bad query.
        401: Unathenticated request.
    """
    # credentials defined in the environment take precedence
    influxdb_username = os.environ.get("INFLUXDB_USERNAME", influxdb_username)
    influxdb_password = os.environ.get("INFLUXDB_PASSWORD", influxdb_password)

    params = {
        "q": f'CREATE DATABASE "{influxdb_database}"',
        "u": influxdb_username,
        "p": influxdb_password,
    }

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


def write_influxdb_line(
    line,
    influxdb_database,
    influxdb_api_url,
    influxdb_username=None,
    influxdb_password=None,
):
    """Write a line to InfluxDB.

    Parameters
    ----------
    line : `str`
        An InfluxDB line formatted according to the line protocol:
        See https://docs.influxdata.com/influxdb/v1.8/write_protocols/

    Returns
    -------
    status_code : `int`
        Status code from the InfluxDB HTTP API.
        204: The request was processed successfully.
        400: Malformed syntax or bad query.
        401: Unathenticated request.
    """
    params = {
        "db": influxdb_database,
        "u": influxdb_username,
        "p": influxdb_password,
    }

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
        401: Unathenticated request.
    """
    influxdb_api_url = f"http://{config.INFLUXDB_API_URL}"
    squash_api_url = f"http://{config.SQUASH_API_URL}"

    status_code = create_influxdb_database(
        config.INFLUXDB_DATABASE, influxdb_api_url
    )

    if status_code != 200:
        message = "Could not create InfluxDB database."
        return message, status_code

    # Get job data from the SQuaSH API
    job_url = f"{squash_api_url}/job/{job_id}"
    try:
        r = requests.get(url=job_url)
        r.raise_for_status()
    except HTTPError:
        message = f"Could not get job {job_id} from the SQuaSH API."
        logger.error(message)
    except ConnectionError:
        message = f"Failed to establish connection with {job_url}."
        logger.error(message)

    status_code = r.status_code

    if status_code != 200:
        message = f"Could not get job {job_id} from the SQuaSH API."
        return message, status_code

    data = r.json()
    transformer = Transformer(squash_api_url=squash_api_url, data=data)

    influxdb_lines = transformer.to_influxdb_line()

    for line in influxdb_lines:
        status_code = write_influxdb_line(
            line, config.INFLUXDB_DATABASE, influxdb_api_url
        )

        if status_code != 204:
            message = f"Error writing job {job_id} to InfluxDB."
            return message, status_code

    message = f"Job {job_id} sucessfully written to InfluxDB."
    return message, status_code
