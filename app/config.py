# http://flask.pocoo.org/docs/0.12/config/#configuration-best-practices

import os

# Set locally for development or obtained from Cloud SQL credentials
# in production (kubernetes deployment)
SQUASH_DB_USER = os.environ.get('SQUASH_DB_USER', '')
SQUASH_DB_PASSWORD = os.environ.get('SQUASH_DB_PASSWORD', '')

# Not used in production (kubernetes deployment)
SQUASH_DB_HOST = os.environ.get('SQUASH_DB_HOST', 'localhost')


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
        "description": "RESTful API for the LSST SQuaSH metrics dashboard. "
                       "You can find out more about SQuaSH at "
                       "https://sqr-009.lsst.io",
        "version": "1.0.0",
        "termsOfService": None,
        "uiversion": 3
    }


class Production(Config):
    """Production configuration"""

    DEBUG = True

    # Default (admin) user
    DEFAULT_USER = os.environ.get('SQUASH_DEFAULT_USER')
    DEFAULT_PASSWORD = os.environ.get('SQUASH_DEFAULT_PASSWORD')

    # Kubernetes deployment with a Cloud SQL instance
    # Because the proxy runs in the cloudsql-proxy containter in the same pod,
    # it appears to the application as localhost
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://{}:{}@127.0.0.1/squash". \
        format(SQUASH_DB_USER, SQUASH_DB_PASSWORD)

    SQLALCHEMY_ECHO = False
    PREFERRED_URL_SCHEME = 'https'


class Development(Config):
    """Development configuration"""

    DEBUG = True

    # Default (dev) user
    DEFAULT_USER = 'mole'
    DEFAULT_PASSWORD = 'desert'

    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:{}@{}/squash_dev". \
        format(SQUASH_DB_PASSWORD, SQUASH_DB_HOST)

    SQLALCHEMY_ECHO = True


class Testing(Config):
    """Testing configuration (for testing client)"""

    DEBUG = True

    # Default (testing) user
    DEFAULT_USER = 'mole'
    DEFAULT_PASSWORD = 'desert'

    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:{}@{}/squash_test". \
        format(SQUASH_DB_PASSWORD, SQUASH_DB_HOST)

    SQLALCHEMY_ECHO = False
