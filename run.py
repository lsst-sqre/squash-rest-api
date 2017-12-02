import os
from app import create_app, db
from app.models import UserModel

if __name__ == '__main__':

    config = os.environ.get('SQUASH_API_CONFIG', "app.config.Development")
    app = create_app(config)

    with app.app_context():
        db.create_all()

        # create a development user
        if UserModel.query.get(1) is None:
            user = UserModel(username="nobody", password="squash")
            user.save_to_db()

    app.run()
