
##################
SQuaSH RESTful API
##################

The SQuaSH RESTful API is a web app implemented in Flask for managing the SQuaSH metrics dashboard. You can learn more about SQuaSH at `SQR-009 <https://sqr-009.lsst.io>`_.

Requirements
============

The SQuaSH RESTful API is deployed as part of the `squash-deployment <https://github.com/lsst-sqre/squash-deployment>`_ and requires a MySQL 5.7 instance on Google Cloud SQL.
We assume this instance exists in the `sqre` project. 

The steps used to connect the `squash-restful-api` app running on GKE with the Google Cloud SQL instance are documented `here <https://cloud.google.com/sql/docs/mysql/connect-kubernetes-engine>`_.
The Service account private key created in this step and referred below as `PROXY_KEY_FILE_PATH` is stored in SQuaRE 1Password repository and identified as *SQuaSH Cloud SQL service account key*.

See also `squash-deployment <https://github.com/lsst-sqre/squash-deployment>`_ on how to configure `kubectl` to access you GKE cluster, use the correct *namespace* for this deployment and create the TLS secrets used
below. 

Kubernetes deployment
---------------------

Assuming you have `kubectl` configured to access your GKE cluster, you can deploy the `squash-restful-api` using:

.. code-block::

 cd squash-restful-api
 
 # Used to create the cloudsql-db-credentials secret
 export PROXY_KEY_FILE_PATH=<path to the JSON file with the SQuaSH Cloud SQL service account key.>
 export SQUASH_DB_PASSWORD=<password created for the proxyuser when the Cloud SQL instance was configured.>
 
 # create secrets with cloud sql proxy key and database password
 make cloudsql-credentials
  
 # The app default user
 export SQUASH_DEFAULT_USER=<the admin user for the production depoyment>
 export SQUASH_DEFAULT_PASSWORD=<password for the admin user>
 
 TAG=latest make service deployment


Debugging
---------

You can inspect the deployment using:

.. code-block::

 kubectl describe deployment squash-restful-api

and the container logs using:

.. code-block::

 kubectl logs deployment/squash-restful-api nginx
 kubectl logs deployment/squash-restful-api api
 kubectl logs deployment/squash-restful-api cloudsql-proxy
 
You can open a terminal inside the `api` container with:

.. code-block::

 kubectl exec -it <TAB> -c api /bin/bash
