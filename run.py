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
import click

from app import create_app, db
from app.models import UserModel

import beeline
from beeline.middleware.flask import HoneyMiddleware


profile = os.environ.get('SQUASH_API_PROFILE', 'app.config.Development')
app = create_app(profile)

honey_api_key = os.environ.get('HONEY_API_KEY')

if honey_api_key:
    beeline.init(writekey=honey_api_key, dataset="squash-rest-api",
                 service_name="squash")
    beeline.add_field('squash_api_profile', profile)
    HoneyMiddleware(app, db_events=True)


@app.cli.command()
def list_routes():
    """List all api routes"""
    click.echo("\n")
    click.echo("{:30s} {:30s} {}".format("View", "Methods", "URL"))
    click.echo("{:30s} {:30s} {}".format("----", "-------", "---"))
    for rule in app.url_map.iter_rules():
        options = {}
        for arg in rule.arguments:
            options[arg] = "[{0}]".format(arg)

        methods = ','.join(rule.methods)
        url = rule.rule
        line = "{:30s} {:30s} {}".format(rule.endpoint, methods, url)
        click.echo(line)

with app.app_context():
    db.create_all()

    # create admin user
    if UserModel.query.get(1) is None:
        user = UserModel(username=app.config['DEFAULT_USER'],
                         password=app.config['DEFAULT_PASSWORD'])
        user.save_to_db()

if __name__ == '__main__':
    app.run()
