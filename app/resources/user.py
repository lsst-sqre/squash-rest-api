from flask_restful import Resource, reqparse
from flask_jwt import jwt_required

from ..models import UserModel


class Register(Resource):

    parser = reqparse.RequestParser()
    parser.add_argument('username',
                        type=str,
                        required=True,
                        help="This field cannot be blank."
                        )

    parser.add_argument('password',
                        type=str,
                        required=True,
                        help="This field cannot be blank."
                        )

    @jwt_required()
    def post(self):
        data = Register.parser.parse_args()

        if UserModel.find_by_username(data['username']):
            return {"message": "A user with that username already exists"}, 400

        user = UserModel(data['username'], data['password'])
        user.save_to_db()

        return {"message": "User created successfully."}, 201


class User(Resource):

    def get(self, username):
        user = UserModel.find_by_username(username)
        if user:
            user.json()
        return {"message": "User not found."}

    @jwt_required()
    def delete(self, username):
        user = UserModel.find_by_username(username)
        if not user:
            return {"message": "Username {} does not exist".format(username)}

        user.delete_from_db()
        return {"message": "User deleted."}


class UserList(Resource):

    def get(self):
        return {"users": [user.json()['username'] for user
                          in UserModel.query.all()]}
