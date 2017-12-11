import unittest
from app import create_app, db
from app.models import UserModel
from .test_client import TestClient

DEFAULT_USERNAME = 'mole'
DEFAULT_PASSWORD = 'desert'


class TestAPI(unittest.TestCase):

    def setUp(self):
        self.app = create_app('app.config.Testing')
        self.context = self.app.app_context()
        self.context.push()

        # refresh testing db
        db.drop_all()
        db.create_all()

        # create default test user
        user = UserModel(DEFAULT_USERNAME, DEFAULT_PASSWORD)
        user.save_to_db()

        # create a testing client
        self.client = TestClient(self.app)

        # set an authentication token for the client
        r, json = self.client.post('/auth',
                                   data={'username': DEFAULT_USERNAME,
                                         'password': DEFAULT_PASSWORD})
        self.client.set_auth(json['access_token'])

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def test_user(self):

        # get list of users
        r, json = self.client.get('/users')
        self.assertTrue(r.status_code == 200)
        self.assertTrue(json['users'] == [DEFAULT_USERNAME])

        # register an user
        data = {'username': 'bob', 'password': 'cat'}
        r, json = self.client.post('/register', data=data)
        self.assertTrue(r.status_code == 201)

        # register an user that already exists
        data = {'username': 'bob', 'password': 'cat'}
        r, json = self.client.post('/register', data=data)
        self.assertTrue(r.status_code == 400)

        # get an authentication token for a registered user
        r, json = self.client.post('/auth', data=data)
        self.assertTrue(r.status_code == 200)

        # delete an user
        r, json = self.client.delete('/user/bob')
        self.assertTrue(r.status_code == 200)

    def test_metric(self):

        # get list of metrics
        r, json = self.client.get('/metrics')
        self.assertTrue(r.status_code == 200)
        self.assertTrue(json['metrics'] == [])

        # add a metric
        r, json = self.client.post('/metric/m1')
        self.assertTrue(r.status_code == 201)

        # delete a metric
        r, json = self.client.delete('/metric/m1')
        self.assertTrue(r.status_code == 200)
        r, json = self.client.get('/metric/m1')
        self.assertTrue(r.status_code == 404)

        # get a metric that does not exist
        r, json = self.client.get('/metric/m1')
        self.assertTrue(r.status_code == 404)

    def test_measurement(self):

        # add a metric
        r, json = self.client.post('/metric/m1')
        self.assertTrue(r.status_code == 201)

        # add measurement
        data = {'value': 1.0, 'metric_name': 'm1', 'data': {'k': 1.0}}

        r, json = self.client.post('/measurement/1', data=data)
        self.assertTrue(r.status_code == 201)

        # add another measurement for an existing job
        data = {'value': 2.0, 'metric_name': 'm1', 'data': {'k': 2.0}}

        r, json = self.client.post('/measurement/1', data=data)
        self.assertTrue(r.status_code == 201)

        # get a measurement from an existing job
        r, json = self.client.get('/measurement/1')
        self.assertTrue(r.status_code == 200)

        # Modify an existing measurement
        # TODO: this doesn't work with multiple measurements, fix resource
        data = {'value': 3.0, 'metric_name': 'm1', 'data': {'k': 3.0}}
        r, json = self.client.put('/measurement/1', data=data)
        self.assertTrue(r.status_code == 202)
        self.assertTrue(json['value'] == 3.0)

        # get a measurement from a job that does not exist
        r, json = self.client.get('/measurement/2')
        self.assertTrue(r.status_code == 404)

        # delete an existing measurement
        # TODO: this doesn't work with multiple measurements, fix resrouce
        r, json = self.client.delete('/measurement/1')
        self.assertTrue(r.status_code == 200)
        # r, json = self.client.get('/measurement/1')
        # self.assertTrue(r.status_code == 404)
