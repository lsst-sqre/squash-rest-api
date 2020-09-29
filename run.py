"""Run the squash-api app.

To run the app in development mode set the following variables:

    export SQUASH_API_PROFILE=app.config.Development
    export FLASK_APP=run:app
    export FLASK_ENV=development
    flask run

If FLASK_ENV is set to development, the flask command will enable debug mode
and `flask run` will enable the interactive debugger and reloader.

See app/config.py for the app configuration.
"""

import os

import click
from app import create_app, db
from app.models import UserModel

profile = os.environ.get("SQUASH_API_PROFILE", "app.config.Development")
app = create_app(profile)


@app.cli.command()
def list_routes():
    """List all api routes."""
    click.echo("\n")
    click.echo("{:30s} {:30s} {}".format("View", "Methods", "URL"))
    click.echo("{:30s} {:30s} {}".format("----", "-------", "---"))
    for rule in app.url_map.iter_rules():
        options = {}
        for arg in rule.arguments:
            options[arg] = "[{0}]".format(arg)

        methods = ",".join(rule.methods)
        url = rule.rule
        line = "{:30s} {:30s} {}".format(rule.endpoint, methods, url)
        click.echo(line)


with app.app_context():
    db.create_all()

    # create admin user
    if UserModel.query.get(1) is None:
        user = UserModel(
            username=app.config["DEFAULT_USER"],
            password=app.config["DEFAULT_PASSWORD"],
        )
        user.save_to_db()
