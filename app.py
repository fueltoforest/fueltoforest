from functools import wraps
import uuid
from datetime import datetime

from flask import Flask, jsonify, request

from bson import ObjectId
from pymongo import Connection, GEO2D

from utils import assert_if, sha1_string, force_utf8, InvalidUsage


app = Flask(__name__)
db = Connection()["fueltoforest"]


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    user_name = data.get('user_name')
    password = data.get('password')
    email = data.get('email')
    assert_if(user_name and len(user_name) > 3 and len(user_name) < 20, "username len >= 4 and < 20 ")
    assert_if(password and len(password) >= 5 and len(password) < 20, "password len > 5 and < 20 ")
    assert_if(email and len(email) >= 3 and len(email) < 50 and '@' in email, "email needed ")

    # check unique
    assert_if(not db.users.find_one(dict(user_name=user_name)), "username not unique")
    assert_if(not db.users.find_one(dict(email=email)), "email not unique")

    hashed_password = sha1_string(force_utf8(password) + "users")
    token = sha1_string(str(uuid.uuid4()))
    user = db.users.insert(dict(
        user_name = user_name,
        email = email,
        password = hashed_password,
        token = token
    ))

    return jsonify(user_name=user_name, token=token)


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    password = data.get('password')
    user_name = data.get('user_name')
    assert_if(user_name, 'username needed')
    assert_if(password, 'password needed')

    hashed_password = sha1_string(force_utf8(password) + "users")

    user = db.users.find_one(dict(
        user_name = user_name,
        password = hashed_password
    ))

    assert_if(user, "password or user_name wrong")

    return jsonify(user_name=user_name, token=user['token'])


@app.route("/rides", methods=['GET'])
def get_rides():
    return jsonify({
        "objects": []
    })


def require_user(fn):
    @wraps(fn)
    def inner():
        try:
            token = request.json['token']
        except:
            token = request.args.get('token')

        assert_if(token, 'token needed for this action')
        user = db.users.find_one(dict(token=token))
        assert_if(user, "token is wrong")
        return fn(user)
    return inner


@app.route("/rides", methods=['POST'])
@require_user
def post_rides(user):
    data = request.json
    user_id = user['_id']
    location = data.get("location")
    inserted_id = db.requests.insert({
        "date_created": datetime.utcnow(),
        "user_id": user_id,
        "start_location": location
    })
    db.places.ensure_index([("location", GEO2D)])
    response = jsonify({
        "ride_id": str(inserted_id)
    })
    response.status_code = 201
    return response


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9910, debug=True)
