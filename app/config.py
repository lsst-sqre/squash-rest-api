# http://flask.pocoo.org/docs/0.12/config/#configuration-best-practices

import os

SQUASH_DB_HOST = os.environ.get("SQUASH_DB_HOST", "localhost")
SQUASH_DB_PASSWORD = os.environ.get("SQUASH_DB_PASSWORD", "")


class Config(object):
    """Base class configuration"""

    APP_DIR = os.path.abspath(os.path.dirname(__file__))

    # Turn off the Flask-SQLAlchemy event system
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Secret key for signing cookies
    SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(32))

    # Swagger configuration for the API documentation
    SWAGGER = {
        "title": "LSST SQuaSH RESTful API",
        "description": "RESTful API for the LSST SQuaSH metrics harness "
                       "system. You can find out more about SQuaSH at "
                       "https://sqr-009.lsst.io",
        "version": "1.0.0",
        "termsOfService": None,
        "uiversion": 3
    }


class Production(Config):
    """Production configuration"""

    DEBUG = False

    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:{}@{}/squash". \
        format(SQUASH_DB_PASSWORD, SQUASH_DB_HOST)

    SQLALCHEMY_ECHO = False


class Development(Config):
    """Development configuration"""

    DEBUG = True

    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:{}@{}/squash_dev". \
        format(SQUASH_DB_PASSWORD, SQUASH_DB_HOST)

    SQLALCHEMY_ECHO = True


class Testing(Config):
    """Testing configuration (for testing client)"""

    DEBUG = True

    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:{}@{}/squash_test". \
        format(SQUASH_DB_PASSWORD, SQUASH_DB_HOST)

    SQLALCHEMY_ECHO = False
