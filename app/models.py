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

    def __init__(self, name, package, display_name, description,
                 unit=None, tags=None, reference=None):

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
    # Id of the metric this specification applies to
    metric_id = db.Column(db.Integer, db.ForeignKey('metric.id'))

    def __init__(self, name, metric_id, threshold=None, tags=None,
                 metadata_query=None):

        self.name = name
        self.metric = metric_id
        self.threshold = threshold
        self.tags = tags
        self.metadata_query = metadata_query

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


class JobModel(db.Model):
    """Database model for lsst.verify metadata
    """

    __tablename__ = 'job'

    STATUS_OK = 0
    STATUS_FAILED = 1

    id = db.Column(db.Integer, primary_key=True)
    # ID of the CI run
    ci_id = db.Column(db.String(32), nullable=False, unique=True)
    # Name of the package than runs through CI, e.g. validate_drp
    ci_name = db.Column(db.String(64), nullable=False)
    # Name of the dataset, e.g cfht
    ci_dataset = db.Column(db.String(32), nullable=False)
    # Name of the platform where the the CI runs, e.g centos-7
    ci_label = db.Column(db.String(64))
    # URL to access the results of the CI run
    ci_url = db.Column(db.Unicode(255))
    # Status of this run 0=ok, 1=failed
    status = db.Column(db.Integer, default=STATUS_OK)

    # Timestamp when the lsst.verify job was created
    date_created = db.Column(db.TIMESTAMP, nullable=False,
                             server_default=now())

    # URL for the git lfs repo for the dataset used in this run
    dataset_repo_url = db.Column(db.Unicode(255))
    # Name of the instrument that collected the dataset used in this run
    instrument = db.Column(db.String(64))
    # Name of the filter associated to this dataset
    filter_name = db.Column(db.String(16))

    # Measurements created by this job, are also deleted
    # upon job deletion
    measurements = db.relationship('MeasurementModel', lazy='dynamic',
                                   cascade="all, delete-orphan")

    def __init__(self, ci_id,
                 ci_name="",
                 ci_dataset="",
                 ci_label="",
                 ci_url="",
                 dataset_repo_url="",
                 instrument="",
                 filter_name=""):

        self.ci_id = ci_id
        self.ci_name = ci_name
        self.ci_dataset = ci_dataset
        self.ci_label = ci_label
        self.ci_url = ci_url
        self.dataset_repo_url = dataset_repo_url
        self.instrument = instrument
        self.filter_name = filter_name

    def json(self):
        return {'ci_id': self.ci_id,
                'measurements': [measurement.json() for measurement
                                 in self.measurements.all()]}
    def json_summary(self):
        return {'ci_id': self.ci_id}

    @classmethod
    def find_by_ci_id(cls, ci_id):
        return cls.query.filter_by(ci_id=ci_id).first()

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
    git_url = db.Column(db.Unicode(255), unique=True)
    # SHA1 hash of the git commit
    git_commit = db.Column(db.String(64), nullable=False)
    # Resolved git branch that the commit resides on
    git_branch = db.Column(db.String(64))
    # EUPS build version
    build_version = db.Column(db.String(64))

    job_id = db.Column(db.Integer, db.ForeignKey('job.id'))

    def __init__(self, name, git_url, git_commit, git_branch,
                 build_version):

        self.name = name
        self.git_url = git_url
        self.git_commit = git_commit
        self.git_branch = git_branch
        self.build_version = build_version

    @classmethod
    def find_by_job(cls, job_id):
        return cls.query.filter_by(job_id=job_id).all()

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

    metric_id = db.Column(db.Integer, db.ForeignKey('metric.id'))
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'))

    def __init__(self, job_id, metric_id, value=None):

        self.job_id = job_id
        self.metric_id = metric_id
        self.value = value

    def json(self):
        return {'value': self.value}

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
