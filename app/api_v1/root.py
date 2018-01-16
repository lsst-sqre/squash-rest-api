from flask import redirect
from flask_restful import Resource


class Root(Resource):
    def get(self):
        return redirect("/apidocs", code=302)
