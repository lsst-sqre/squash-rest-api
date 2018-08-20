Test data
=========

``Cfht_output_r.json``: an output of validate_drp obtained from Jenkins CI artifacts
``job-768.json``: a transformed job using squash-migrator ETL tool
``verify_job.json``: a verification job created using this command line from a lsstsw installation:

..code-block::

  $ dispatch_verify.py --test --env jenkins --lsstsw $(pwd) Cfht_output_r.json --write verify_job.json


