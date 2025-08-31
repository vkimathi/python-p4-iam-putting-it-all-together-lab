from flask import Flask, request, session, jsonify
from flask_restful import Api, Resource
from flask_migrate import Migrate
from flask_cors import CORS

from models import db, User, Recipe

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "super-secret-key" 

db.init_app(app)
migrate = Migrate(app, db)
api = Api(app)
CORS(app, supports_credentials=True)


class Signup(Resource):
    def post(self):
        data = request.get_json()
        try:
            user = User(
                username=data["username"],
                image_url=data.get("image_url"),
                bio=data.get("bio"),
            )
            user.password_hash = data["password"]
            db.session.add(user)
            db.session.commit()

            session["user_id"] = user.id

            return user.to_dict(), 201
        except Exception as e:
            return {"errors": [str(e)]}, 422


class CheckSession(Resource):
    def get(self):
        user_id = session.get("user_id")
        if not user_id:
            return {"error": "Unauthorized"}, 401

        user = db.session.get(User, user_id)
        if not user:
            return {"error": "Unauthorized"}, 401

        return user.to_dict(), 200


class Login(Resource):
    def post(self):
        data = request.get_json()
        user = User.query.filter_by(username=data.get("username")).first()

        if user and user.authenticate(data.get("password")):
            session["user_id"] = user.id
            return user.to_dict(), 200
        return {"error": "Invalid username or password"}, 401


class Logout(Resource):
    def delete(self):
        if session.get("user_id"):
            session.pop("user_id")
            return "", 204
        return {"error": "Unauthorized"}, 401


class RecipeIndex(Resource):
    def get(self):
        if not session.get("user_id"):
            return {"error": "Unauthorized"}, 401

        recipes = Recipe.query.all()
        return [recipe.to_dict() for recipe in recipes], 200

    def post(self):
        user_id = session.get("user_id")
        if not user_id:
            return {"error": "Unauthorized"}, 401

        data = request.get_json()
        try:
            recipe = Recipe(
                title=data["title"],
                instructions=data["instructions"],
                minutes_to_complete=data["minutes_to_complete"],
                user_id=user_id,
            )
            db.session.add(recipe)
            db.session.commit()

            return recipe.to_dict(), 201
        except Exception as e:
            return {"errors": [str(e)]}, 422

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)