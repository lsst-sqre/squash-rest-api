##########
SQuaSH API
##########

REST API for managing SQuaSH metrics. You can learn more about SQuaSH in `SQR-009 <https://sqr-009.lsst.io>`_.


Deployment
==========

The SQuaSH API is deployed as part of the `Science Platform <https://github.com/lsst-sqre/lsp-deploy>`_. The SQuaSH API Helm chart is maintained in the `lsst-sqre charts repository <https://github.com/lsst-sqre/charts/tree/master/charts/squash-api>`_.

We assume you are familiar with the SQuaSH MySQL 5.7 instances on Google Cloud SQL. There's an instance for each SQuaSH environment, ``sandbox`` and ``prod``. Such instances exist under the ``sqre`` project on Google Platform, and the `service account <https://cloud.google.com/sql/docs/mysql/connect-kubernetes-engine>`_ key can be found on SQuaRE 1Password (search for *SQuaSH Cloud SQL service account key*).


Development workflow
====================

1. Clone the repository

.. code-block::

 git clone  https://github.com/lsst-sqre/squash-api.git
 cd squash-api

2. Install the dependencies

.. code-block::

 virtualenv venv -p python3

Activate the Flask app and set development mode in your environment

.. code-block::

 echo "export FLASK_APP=squash.app:app" >> venv/bin/activate
 echo "export FLASK_ENV=development" >> venv/bin/activate

 source venv/bin/activate
 make update

3. Initialize local instances of MySQL, Redis, and Celery for development

.. code-block::

 export SQUASH_DB_PASSWORD=<squash db mysql password>
 make mysql
 make dropdb  # if there's a previous db in there
 make createdb
 <new terminal session>
 make redis
 <new terminal session>
 make celery


The celery task `squash.tasks.s3.upload_object` requires the `AWS credentials present in the environment <https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html>`_. It assumes the the `s3://squash-dev.data/` S3 bucket was previously created.
 
4. Run the app locally

Note that by default the app will run using the development config profile, which is equivalent to do:

.. code-block::

 flask run

The app will run at http://localhost:5000


5. Run tests

.. code-block::

 coverage run --source=src/squash test.py

You can also exercise the API running the `test API notebook <https://github.com/lsst-sqre/squash-rest-api/blob/master/tests/test_api.ipynb>`_.
