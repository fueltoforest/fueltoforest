from functools import wraps
import uuid
from geopy import distance, Point

from datetime import datetime

from flask import Flask, jsonify, request, render_template

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
    def inner(*args, **kwargs):
        try:
            token = request.json['token']
        except:
            token = request.args.get('token')

        assert_if(token, 'token needed for this action')
        user = db.users.find_one(dict(token=token))
        assert_if(user, "token is wrong")
        return fn(user, *args, **kwargs)
    return inner

@app.route("/rides", methods=['POST'])
@require_user
def post_rides(user):
    data = request.json
    user_id = user['_id']
    location = data.get("location")
    inserted_id = db.rides.insert({
        "date_created": datetime.utcnow(),
        "user_id": user_id,
        "start_location": location,
        'status': 'started'
    })
    db.rides.ensure_index([("start_location", GEO2D)])
    response = jsonify({
        "ride_id": str(inserted_id)
    })
    response.status_code = 201
    return response


@app.route("/rides/<id>/heartbeat", methods=['POST'])
@require_user
def heartbeat(user, id):
    """
    Handles users current location
    """
    data = request.json
    user_id = user['_id']
    location = data.get("location")
    db.rides.ensure_index([("current_location", GEO2D)])
    db.ride_routes.ensure_index([("current_location", GEO2D)])

    ride = db.rides.find_one({'_id': ObjectId(id)})
    assert ride
    assert ride['user_id'] == user_id

    db.rides.update({'_id': ObjectId(id)}, {'$set':{'current_location': location, 'last_update': datetime.utcnow()}})
    db.ride_routes.insert({'current_location': location, 'created_at': datetime.utcnow(),
                           'ride_id': id})

    response = jsonify({
        "ride_id": str(id)
    })
    response.status_code = 200
    return response

def calc_ride_distance(ride_id):
    locs = db.ride_routes.find({'ride_id': ride_id}).sort('created_at', -1)
    last_p = None
    dis = 0
    for loc in locs:
        print "loc::::", loc
        lon, lat = loc['current_location']
        p = Point(latitude=lat, longitude=lon)
        if last_p:
            print ">>>>", dis
            dis += distance.distance(last_p, p).km
        last_p = p
    return dis


def calc_donate(kms):
    """
    TODO: tamamen scientific user behaviour driven calculation yapiyoruz,

    km basina 10 kurus, sonra TL ye ceviriyoruz,
    30 km ~ 3 lira yapiyor
    60 km ~ 7 lira yapiyor (exponantial olarak artiyor,
                            km arttikca bagis oranin fazlalasiyor ki araci daha az kullanmak isteyesin)
    >>> calc_donate(30)
    3.0
    >>> calc_donate(60)
    7.0
    >>> calc_donate(90)
    10.0
    """
    kms = (kms * 1.1)
    r =  (kms * 10) / 100
    if r < 1:
        return 1
    return round(r)

@app.route("/rides/<id>/finish", methods=['POST'])
@require_user
def finish_ride(user, id):
    """
    Finishes the ride
    """
    data = request.json
    user_id = user['_id']
    location = data.get("location")
    db.rides.ensure_index([("current_location", GEO2D)])
    db.ride_routes.ensure_index([("current_location", GEO2D)])

    ride = db.rides.find_one({'_id': ObjectId(id)})
    assert ride
    assert ride['user_id'] == user_id

    db.ride_routes.insert({'current_location': location, 'created_at': datetime.utcnow(),
                           'ride_id': id})
    db.rides.update({'_id': ObjectId(id)}, {'$set':{'end_location': location, 'status': 'finished'}})

    dis = calc_ride_distance(ride_id=id)

    response = jsonify({
        "ride_id": str(id),
        "distance": dis,
        "donate": calc_donate(kms=dis)
    })
    response.status_code = 200
    return response


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9910, debug=True)
