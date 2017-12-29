import numpy as np
import json

from .db import db
from werkzeug.security import generate_password_hash, check_password_hash

# Implements JSON data type in MySQL 5.7 see
# https://jira.lsstcorp.org/browse/DM-12191
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.sql import expression
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.mysql import TIMESTAMP


# https://jira.lsstcorp.org/browse/DM-12193
class now(expression.FunctionElement):
    type = TIMESTAMP


@compiles(now, 'mysql')
def mysql_now(element, compiler, **kw):
    return "CURRENT_TIMESTAMP()"


class UserModel(db.Model):
    """Database model for authenticated API users."""

    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True,
                         index=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        """Verify the user password against the password hash saved
        in the database."""

        return check_password_hash(self.password_hash, password)

    def json(self):
        return {'username': self.username}

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()


class MetricModel(db.Model):
    """Database model for metrics as defined
    in the lsst.verify package. See https://sqr-019.lsst.io/
    """

    __tablename__ = 'metric'

    id = db.Column(db.Integer, primary_key=True)
    # Full qualified name of the metric including the package
    # name, e.g. validate_drp.AM1
    name = db.Column(db.String(64), nullable=False, unique=True)
    # Name of the package that defines this metric, e.g. validate_drp
    package = db.Column(db.String(64))
    # Display name of the metric, e.g. `AM1`
    display_name = db.Column(db.String(64))
    # Short description about the metric.
    description = db.Column(db.Text())
    # Units of the metric. String representation of an astropy unit.
    # An empty string means an unitless quantity.
    unit = db.Column(db.String(16))
    # Tags associated with this metric. Tags are strings
    # that can be used to group metrics.
    tags = db.Column(JSON())
    # Reference to the original document that defines the metric
    # usually with a handle to the document, its url and page number.
    reference = db.Column(JSON())

    specification = db.relationship('SpecificationModel')
    measurement = db.relationship('MeasurementModel')

    def __init__(self, name, package=None, display_name=None,
                 description=None, unit=None, tags=None,
                 reference=None):

        self.name = name
        self.package = package
        self.display_name = display_name
        self.description = description
        self.package = package
        self.unit = unit
        self.tags = tags
        self.reference = reference

    def json(self):
        return {'name': self.name,
                'package': self.package,
                'display_name': self.display_name,
                'description': self.description,
                'unit': self.unit,
                'tags': self.tags,
                'reference': self.reference}

    @classmethod
    def find_by_name(cls, name):
        return cls.query.filter_by(name=name).first()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()


class SpecificationModel(db.Model):
    """Database model for metric specifications as defined
    in the lsst.verify package. See https://sqr-019.lsst.io/
    """

    __tablename__ = 'spec'

    id = db.Column(db.Integer, primary_key=True)
    # Full qualified name of the specification, e.g.
    # validate_drp.AM1.minimum_gri
    name = db.Column(db.String(64), nullable=False)
    # Defines the specification, usually the threshold
    # field has an operator, value and unit keys.
    threshold = db.Column(JSON())
    # Tags associated with this specification
    tags = db.Column(JSON())
    # Additional metadata information that can be tested
    # against the job metadata
    metadata_query = db.Column(JSON())
    # Type of specification
    type = db.Column(db.String(64))

    # Id of the metric this specification applies to
    metric_id = db.Column(db.Integer, db.ForeignKey('metric.id'))

    def __init__(self, name, metric_id, threshold=None, tags=None,
                 metadata_query=None, type=None):

        self.name = name
        self.metric = metric_id
        self.threshold = threshold
        self.tags = tags
        self.metadata_query = metadata_query
        self.type = type

    def json(self):
        return {'name': self.name,
                'threshold': self.threshold,
                'tags': self.tags,
                'metadata_query': self.metadata_query}

    @classmethod
    def find_by_name(cls, name):
        return cls.query.filter_by(name=name).first()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()


class EnvModel(db.Model):
    """Database model for environment data,
    it has a one-to-many relationship with JobModel """

    __tablename__ = 'env'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    display_name = db.Column(db.String(64), nullable=False)

    job = db.relationship("JobModel", lazy="dynamic")

    def __init__(self, name):

        self.name = name
        self.display_name = name

    def json(self):
        return {'name': self.name,
                'display_name': self.display_name}

    @classmethod
    def find_by_name(cls, env_name):
        return cls.query.filter_by(name=env_name).first()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()


class JobModel(db.Model):
    """Database model for lsst.verify Job

    Job has a one-to-many relationship with PackageModel,
    MeasurementModel and BlobModel and a one-to-one relationship
    with EnvModel.
    """

    __tablename__ = 'job'

    # SQLAlchemy automatically set the first integer PK column
    # that's not marked as a FK as autoincrement=True.
    id = db.Column(db.Integer, primary_key=True)

    # Id of the environment this job has run
    env_id = db.Column(db.Integer, db.ForeignKey('env.id'))

    # Timestamp when the lsst.verify job was created
    date_created = db.Column(db.TIMESTAMP, nullable=False,
                             server_default=now())
    env = db.Column(JSON())
    meta = db.Column(JSON())

    # Measurements are deleted upon job deletion
    measurements = db.relationship("MeasurementModel", lazy="dynamic",
                                   cascade="all, delete-orphan")

    # Packages are deleted upon job deletion
    packages = db.relationship("PackageModel", lazy="dynamic",
                               cascade="all, delete-orphan")

    # Blobs are also deleted upon job deletion
    blobs = db.relationship("BlobModel", lazy="dynamic",
                            cascade="all, delete-orphan")

    def __init__(self, env_id, env, meta):

        self.env_id = env_id
        self.env = env
        self.meta = meta

    def json(self):

        # Reconstruct the lsst.verify job metadata
        self.meta['packages'] = [pkg.json() for pkg in self.packages.all()]
        self.meta['env'] = self.env

        return {'measurements': [meas.json() for meas in
                                 self.measurements.all()],
                'blobs': [blob.json() for blob in
                          self.blobs.all()],
                'meta': self.meta}

    @classmethod
    def find_by_id(cls, job_id):
        return cls.query.filter_by(id=job_id).first()

    @classmethod
    def find_by_env_data(cls, env_id, key, value):

        # JSON field expression
        e = cls.env[key] == value
        return cls.query.filter_by(env_id=env_id).filter(e).first()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()


class PackageModel(db.Model):
    """A specific version of an eups package used
    by the lsst.verify job"""

    __tablename__ = 'package'

    id = db.Column(db.Integer, primary_key=True)
    # EUPS package name
    name = db.Column(db.String(64), nullable=False)
    # URL of the git repository for this package
    git_url = db.Column(db.Unicode(255))
    # SHA1 hash of the git commit
    git_sha = db.Column(db.String(64), nullable=False)
    # Resolved git branch that the commit resides on
    git_branch = db.Column(db.String(64))
    # EUPS build version
    eups_version = db.Column(db.String(64))

    job_id = db.Column(db.Integer, db.ForeignKey('job.id'))

    def __init__(self, job_id, name, git_url, git_sha, git_branch=None,
                 eups_version=None):

        self.job_id = job_id
        self.name = name
        self.git_url = git_url
        self.git_sha = git_sha
        self.git_branch = git_branch
        self.eups_version = eups_version

    def json(self):
        return {'name': self.name,
                'git_url': self.git_url,
                'git_sha': self.git_sha,
                'git_branch': self.git_branch,
                'eups_version': self.eups_version}

    @classmethod
    def find_by_job_id(cls, job_id):
        return cls.query.filter_by(job_id=job_id).first()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()


class MeasurementModel(db.Model):
    """Database model for metric measurements"""

    __tablename__ = 'measurement'

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Float)
    # Full qualified name of the metric including the package
    # name, e.g. validate_drp.AM1
    metric_name = db.Column(db.String(64), nullable=False)
    # Unit of the measurement
    unit = db.Column(db.String(16), nullable=False)

    metric_id = db.Column(db.Integer, db.ForeignKey('metric.id'))
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'))

    def __init__(self, job_id, metric_id, value=0, unit=None,
                 metric='', identifier=None, blob_refs=None):

        self.job_id = job_id
        self.metric_id = metric_id

        # FIX: review this
        # handle nan in measurement values
        if np.isnan(float(value)):
            value = 0

        self.value = value
        self.metric_name = metric
        self.unit = unit

    def json(self):
        return {'value': self.value,
                'unit': self.unit,
                'metric': self.metric_name}

    @classmethod
    # A job can have multiple measurements
    def find_by_job_id(cls, job_id):
        return cls.query.filter_by(job_id=job_id).all()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()


class BlobModel(db.Model):
    """Database model for data blobs"""

    __tablename__ = 'blob'

    id = db.Column(db.Integer, primary_key=True)
    # Receives a string representation of python UUID object
    # and store as CHAR(32)
    identifier = db.Column(db.String(32), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    data = db.Column(JSON())

    job_id = db.Column(db.Integer, db.ForeignKey('job.id'))

    def __init__(self, job_id, identifier, name, data):

        self.job_id = job_id
        self.identifier = identifier
        self.name = name

        # FIX: review this
        # handle nan values in data blobs

        self.data = json.loads(json.dumps(data).replace("NaN", "0"))

    def json(self):
        return {'identifier': self.identifier,
                'name': self.name,
                'data': self.data}

    @classmethod
    # A job can have multiple measurements
    def find_by_identifier(cls, identifier):
        return cls.query.filter_by(identifier=identifier).first()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
