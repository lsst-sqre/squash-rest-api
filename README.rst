
##################
SQuaSH RESTful API
##################

The SQuaSH RESTful API is a web app implemented in Flask for managing the SQuaSH metrics dashboard. You can learn more about SQuaSH at `SQR-009 <https://sqr-009.lsst.io>`_.

Requirements
============

The SQuaSH RESTful API is part of the `squash-deployment <https://github.com/lsst-sqre/squash-deployment>`_ follow
the steps on that link to configure `kubectl` to access you GKE cluster, use the correct *namespace* for this deployment and create the TLS certificates used below.


The `squash-restful-api` requires a MySQL 5.7 instance on Google Cloud SQL. We assume such instance exists in the `sqre` project and that you have created a service account private key as described `here <https://cloud.google.com/sql/docs/mysql/connect-kubernetes-engine>`_.

NOTE: The Service account private key created at this step is referred below as `PROXY_KEY_FILE_PATH`, and is stored in SQuaRE 1Password account identified as *SQuaSH Cloud SQL service account key*.


Kubernetes deployment
---------------------


Assuming all the requirements above are satisfied and that you are using the namespace `demo`:

.. code-block::

 cd squash-restful-api

 # Create secret with the Cloud SQL Proxy key and the database password
 export PROXY_KEY_FILE_PATH=<path to the JSON file with the SQuaSH Cloud SQL service account key.>
 export SQUASH_DB_PASSWORD=<password created for the user `proxyuser` when the Cloud SQL instance was configured.>
 make cloudsql-secret

 # Name of the Cloud SQL instance to use
 export INSTANCE_CONNECTION_NAME=<name of the cloudsql instance>

 # Create secret with AWS credentials
 export AWS_ACCESS_KEY_ID=<the aws access key id>
 export AWS_SECRET_ACCESS_KEY=<the aws secret access key>
 make aws-secret

 # Create the S3 bucket for this deployment
 make s3-bucket

 # Set the application default user
 export SQUASH_DEFAULT_USER=<the squash api admin user>
 export SQUASH_DEFAULT_PASSWORD=<password for the squash api admin user>

 TAG=latest make service deployment

 # Create the service name
 cd ..

 export SQUASH_SERVICE=squash-restful-api
 make name

The SQuaSH RESTful API should be available through the URL created in the previous step.


Debug
^^^^^

You can inspect the deployment using:

.. code-block::

 kubectl describe deployment squash-restful-api

and the container logs using:

.. code-block::

 kubectl logs deployment/squash-restful-api nginx
 kubectl logs deployment/squash-restful-api api
 kubectl logs deployment/squash-restful-api worker
 kubectl logs deployment/squash-restful-api redis
 kubectl logs deployment/squash-restful-api cloudsql-proxy

You can open a terminal inside the `api` container with:

.. code-block::

 kubectl exec -it <TAB> -c api /bin/bash

and connect to the database with  `mysql -h 127.0.0.1 -u proxyuser -p`.

NOTE: Due to initialization of the containers it might happen that the `api` container tries
to connect to the Cloud SQL instance before the `cloudsql-proxy` container is initialized, one
way to fix that is to restart only the `api` container in the pod.

The following kill all processes, and the `api` container will restart.

.. code-block::

 kubectl exec <squash-restful-api pod> -c api /sbin/killall5

Development workflow
--------------------


1. Install the software dependencies

.. code-block::

 git clone  https://github.com/lsst-sqre/squash-restful-api.git
 cd squash-restful-api

 virtualenv env -p python3

 # Activate the Flask cli and debugger in your environment
 echo "export FLASK_APP=run.py" >> env/bin/activate
 echo "export FLASK_DEBUG=1" >> env/bin/activate

 source env/bin/activate
 pip install -r requirements.txt

2. Initialize the MySQL, Redis, and Celery instances for development

.. code-block::

 export SQUASH_DB_PASSWORD=<squash db mysql password>
 make mysql
 make dropdb  # if there's a previous db in there
 make createdb
 <new terminal session>
 make redis
 <new terminal session>
 make celery

3. Run tests

.. code-block::

 coverage run --source=app test.py

4. Run the app locally:

Note that by default the app will run using the development config profile, which is equivalent to do:

.. code-block::

 export SQUASH_API_PROFILE=app.config.Development
 flask run

or check the available commands with

.. code-block::

 flask --help

The app will run at http://localhost:5000

5. Exercise the API running the `test API notebook <https://github.com/lsst-sqre/squash-rest-api/blob/master/tests/test_api.ipynb>`_.
