#!/usr/bin/env python

"""Run the squash-restful-api in development or production mode.

To run in development mode:

  ./run.py

In production mode, the kubernetes configuration will set the env variable:

  export SQUASH_API_PROFILE=app.config.Production

and the app will run under the uwsgi server calling this script:

  ./run.py

See app/config.py for the corresponding configuration.
"""

import os

from app import create_app, db
from app.models import UserModel

profile = os.environ.get('SQUASH_API_PROFILE', 'app.config.Development')
app = create_app(profile)

with app.app_context():
    db.create_all()

    # create admin user
    if UserModel.query.get(1) is None:
        user = UserModel(username=app.config['DEFAULT_USER'],
                         password=app.config['DEFAULT_PASSWORD'])
        user.save_to_db()

if __name__ == '__main__':
    app.run()
