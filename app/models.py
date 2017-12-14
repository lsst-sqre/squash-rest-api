from .db import db
from werkzeug.security import generate_password_hash, check_password_hash

# Implements JSON data type in MySQL 5.7 see
# https://jira.lsstcorp.org/browse/DM-12191
from sqlalchemy.dialects.mysql import JSON


class UserModel(db.Model):
    """Database model for authenticated API users."""

    __tablename__ = 'users'

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
    """Database model for squash metrics as defined
    in the lsst.verify package. See https://sqr-019.lsst.io/

    name : `str`
        Name of the metric.
    description : `str`
        Short description about the metric.
    unit : `str`
        Units of the metric. String representation of an astropy unit.
        An empty string means an unitless quantity.
    tags : `list`
        Tags associated with this metric. Tags are strings
        that can be used to group metrics.
    reference: `dict`, optional
        reference to the original document that defines the metric
        usually with a handle to the document, its url and page number.
    package: name of the package that defines this metric
    """

    __tablename__ = 'metrics'

    id = db.Column(db.Integer, primary_key=True)
    # name of the metric
    name = db.Column(db.String(64), nullable=False)
    # short description about the metric
    description = db.Column(db.Text())
    # name of the package that defines the metric
    package = db.Column(db.String(64), nullable=False)
    # units of the metric
    unit = db.Column(db.String(16))
    # tags associated with the metric
    tags = db.Column(JSON())
    # reference to the original doc that defines the metric
    reference = db.Column(JSON())

    specification = db.relationship('SpecificationModel')

    def __init__(self, name, description, package, unit=None,
                 tags=None, reference=None):
        self.name = name
        self.description = description
        self.package = package
        self.unit = unit
        self.tags = tags
        self.reference = reference

    def json(self):
        return {'name': self.name,
                'description': self.description,
                'package': self.package,
                'unit': self.unit,
                'tags': self.tags,
                'reference': self.reference}

    @classmethod
    def find_by_name(cls, name):
        return cls.query.filter_by(name=name).all()

    @classmethod
    def find_by_fqn(cls, package, name):
        return cls.query.filter_by(package=package, name=name).first()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()


class SpecificationModel(db.Model):
    """Database model for metrics specifications as defined
    in the lsst.verify package. See https://sqr-019.lsst.io/

    id: `int`
        Id of the specification
    name : `str`
        Name of the specification
    metric_id : `integer`
        Id of the metric this specification applies to
    threshold : `dict`
        defines the specification, usually the threshold
        field has an operator, value and unit keys.
    tags : `list`
        Tags associated with this specification
    metadata_query: `dict`
        Additional metadata information that can be tested
        against the job metadata
    """

    __tablename__ = 'specifications'

    # id of the specification
    id = db.Column(db.Integer, primary_key=True)
    # name of the specification
    name = db.Column(db.String(64), nullable=False)
    # id of the metric this specification applies to
    metric_id = db.Column(db.Integer, db.ForeignKey('metrics.id'))
    # defines the specification test
    threshold = db.Column(JSON())
    # tags associated with this specification
    tags = db.Column(JSON())
    # additional metadata information
    metadata_query = db.Column(JSON())

    def __init__(self, name, metric_id, threshold=None, tags=None,
                 metadata_query=None):

        self.name = name
        self.metric_id = metric_id
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


class MeasurementModel(db.Model):
    """Database model for measurements of squash metrics.

    This implementation provides a minimal model to test the
    JSON data type.
    """

    __tablename__ = 'measurements'

    id = db.Column(db.Integer, primary_key=True)
    job = db.Column(db.String(80))
    value = db.Column(db.Float())
    data = db.Column(JSON())

    def __init__(self, metric_name, job, value, data):

        metric = MetricModel.find_by_name(metric_name)

        if metric:
            self.metric_id = metric.id
        else:
            return {'message': 'Metric {} not found.'.format(metric_name)}, 404

        self.job = job
        self.value = value
        self.data = data

    def json(self):
        return {'job': self.job, 'value': self.value, 'data': self.data}

    @classmethod
    def find_by_job(cls, job):
        return cls.query.filter_by(job=job).first()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
