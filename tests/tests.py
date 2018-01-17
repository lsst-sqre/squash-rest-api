import unittest
from app import create_app, db
from app.models import UserModel
from .test_client import TestClient


class TestAPI(unittest.TestCase):

    def setUp(self):
        self.app = create_app('app.config.Testing')
        self.context = self.app.app_context()
        self.context.push()

        self.user = self.app.config['DEFAULT_USER']
        self.password = self.app.config['DEFAULT_PASSWORD']

        # refresh testing db
        db.drop_all()
        db.create_all()

        # create default test user
        user = UserModel(self.user, self.password)
        user.save_to_db()

        # create a testing client
        self.client = TestClient(self.app)

        # set an authentication token for the client
        user = {'username': self.user, 'password': self.password}
        r, json = self.client.post('/auth', data=user)
        self.client.set_auth(json['access_token'])

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def test_root(self):

        # test API root url
        r, json = self.client.get('/')
        self.assertTrue(r.status_code == 200)

    def test_user(self):

        # get list of users
        r, json = self.client.get('/users')
        self.assertTrue(r.status_code == 200)
        self.assertTrue(json['users'] == [self.user])

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
        data = {'description': 'string',
                'tags': ['a', 'b', 'c']}
        r, json = self.client.post('/metric/demo.m1', data=data)
        self.assertTrue(r.status_code == 201)

        # delete a metric
        r, json = self.client.delete('/metric/demo.m1')
        self.assertTrue(r.status_code == 200)
        r, json = self.client.get('/metric/demo.m1')
        self.assertTrue(r.status_code == 404)

        # get a metric that does not exist
        r, json = self.client.get('/metric/demo.m1')
        self.assertTrue(r.status_code == 404)

    def test_job(self):

        data = {
            'measurements': [],
            'blobs': [],
            'meta': {
                'ci_name': 'string',
                'ci_dataset': 'string',
                'ci_url': 'string',
                'env': {'env_name': 'string'},
                'packages': []
            }
        }

        # add a job
        r, json = self.client.post('/job', data=data)
        self.assertTrue(r.status_code == 201)

        # delete a job
        r, json = self.client.delete('/job/1')
        self.assertTrue(r.status_code == 200)

        # delete a job that does not exist
        r, json = self.client.delete('/job/1')
        self.assertTrue(r.status_code == 404)

    def test_measurement(self):

        # add a metric
        data = {'description': 'string'}

        r, json = self.client.post('/metric/demo.m1', data=data)
        self.assertTrue(r.status_code == 201)

        data = {
            'measurements': [],
            'blobs': [],
            'meta': {
                'ci_name': 'string',
                'ci_dataset': 'string',
                'ci_url': 'string',
                'env': {'env_name': 'string'},
                'packages': []
            }
        }

        # add a job
        r, json = self.client.post('/job', data=data)
        self.assertTrue(r.status_code == 201)

        # add measurement
        data = {'value': 1.0, 'metric': 'demo.m1', 'unit': 'unknown'}

        r, json = self.client.post('/measurement/1', data=data)
        self.assertTrue(r.status_code == 201)

        # add another measurement for an existing job
        data = {'value': 2.0, 'metric': 'demo.m1', 'unit': 'unknown'}

        r, json = self.client.post('/measurement/1', data=data)
        self.assertTrue(r.status_code == 201)

        # get measurements from an existing job
        r, json = self.client.get('/measurement/1')
        self.assertTrue(r.status_code == 200)

        # get measurements from a job that does not exist
        r, json = self.client.get('/measurement/2')
        self.assertTrue(r.status_code == 404)
