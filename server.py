import flask
from flask import Response, jsonify, request
from flask.views import MethodView
from sqlalchemy.exc import IntegrityError

from models import Session, User
app = flask.Flask("app")

class HttpError(Exception):
    def __init__(self, status_code: int, description: str):
        self.status_code = status_code
        self.description = description


@app.errorhandler(HttpError)
def error_handler(error):
    response = jsonify({"error": error.description})
    response.status_code = error.status_code
    return response


@app.before_request
def before_request():
    session = Session()
    request.session = session


@app.after_request
def after_request(response: Response):
    request.session.close()
    return response


def get_user(user_id: int):
    user = request.session.get(User, user_id)
    if user is None:
        raise HttpError(404, "user not found")
    return user


def add_user(user: User):
    try:
        request.session.add(user)
        request.session.commit()
    except IntegrityError as err:
        raise HttpError(409, "user already exists")
    return user


class UserView(MethodView):
    @property
    def session(self) -> Session:
        return request.session

    def get(self, user_id: int):
        user = get_user(user_id)
        return jsonify(
            {
                "id": user.id,
                "author": user.author,
                "title": user.title,
                "description": user.description,
                "created_at": user.created_at.isoformat(),
            }
        )

    def post(self):
        user_data = request.json
        new_user = User(**user_data)
        new_user = add_user(new_user)
        return jsonify({"id": new_user.id})

    def patch(self, user_id: int):
        user_data = request.json
        user = get_user(user_id)
        for key, value in user_data.items():
            setattr(user, key, value)
        user = add_user(user)
        return jsonify(
            {
                "id": user.id,
                "author": user.author,
                "title": user.title,
                "description": user.description,
                "created_at": user.created_at.isoformat(),
            }
        )

    def delete(self, user_id: int):
        user = get_user(user_id)
        self.session.delete(user)
        self.session.commit()
        return jsonify({"status": "ok"})


user_view = UserView.as_view("user_view")

app.add_url_rule(
    "/user/<int:user_id>", view_func=user_view, methods=["GET", "PATCH", "DELETE"]
)
app.add_url_rule("/user", view_func=user_view, methods=["POST"])


if __name__ == "__main__":
    app.run(debug=True)